#!/usr/bin/env python3
"""nRouter SDK & Provider Health Sentinel Aggregator and Dashboard Generator.

Aggregates individual SDK canary outputs, performs automated failure triage,
generates machine-readable reports (JSON, CSV), renders the unified GitHub Pages
dashboard, and writes GitHub Actions Step Summary.

Usage:
    python3 scripts/aggregate_sentinel.py --self-test
    python3 scripts/aggregate_sentinel.py --fixture --output-dir dist/
    python3 scripts/aggregate_sentinel.py --results-dir results/ --output-dir dist/
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

ROOT = Path(__file__).resolve().parent.parent


@dataclass
class TriageVerdict:
    category: str  # "ALL_OPERATIONAL", "SDK_REGRESSION", "PROVIDER_OUTAGE_OR_QUOTA", "GATEWAY_OR_AUTH_DOWN", "PARTIAL_DEGRADATION"
    severity: str  # "info", "warning", "critical"
    diagnosis: str
    affected_sdks: List[str]
    affected_providers: List[str]


def evaluate_triage(results: List[Dict[str, Any]]) -> TriageVerdict:
    """Analyze failures across SDKs and providers to diagnose the failure mode."""
    if not results:
        return TriageVerdict(
            category="ALL_OPERATIONAL",
            severity="info",
            diagnosis="No test results recorded.",
            affected_sdks=[],
            affected_providers=[],
        )

    failed_results = [r for r in results if r.get("status") == "failed"]
    passed_results = [r for r in results if r.get("status") == "passed"]

    if not failed_results:
        return TriageVerdict(
            category="ALL_OPERATIONAL",
            severity="info",
            diagnosis="All 10 SDKs and tested providers are healthy and operational.",
            affected_sdks=[],
            affected_providers=[],
        )

    failed_sdks = sorted(list({r.get("sdk") for r in failed_results if r.get("sdk")}))
    failed_providers = sorted(list({r.get("provider") for r in failed_results if r.get("provider")}))
    passed_providers = sorted(list({r.get("provider") for r in passed_results if r.get("provider")}))

    # Case 1: All SDKs failed
    if len(failed_results) == len(results):
        return TriageVerdict(
            category="GATEWAY_OR_AUTH_DOWN",
            severity="critical",
            diagnosis=(
                f"All {len(results)} SDK tests failed across all providers ({', '.join(failed_providers)}). "
                "Diagnosis: Core nRouter Gateway edge failure, network/DNS outage, or invalid Sentinel virtual API key."
            ),
            affected_sdks=failed_sdks,
            affected_providers=failed_providers,
        )

    # Case 2: Specific Provider Outage
    # If all failures belong to one provider and other providers succeeded
    provider_fail_counts: Dict[str, int] = {}
    provider_total_counts: Dict[str, int] = {}
    for r in results:
        p = r.get("provider", "unknown")
        provider_total_counts[p] = provider_total_counts.get(p, 0) + 1
        if r.get("status") == "failed":
            provider_fail_counts[p] = provider_fail_counts.get(p, 0) + 1

    dead_providers = [
        p for p, fails in provider_fail_counts.items()
        if fails == provider_total_counts[p] and fails >= 1 and passed_providers
    ]

    if dead_providers and not any(p not in dead_providers for p in failed_providers):
        return TriageVerdict(
            category="PROVIDER_OUTAGE_OR_QUOTA",
            severity="warning",
            diagnosis=(
                f"All tests for provider(s) '{', '.join(dead_providers)}' failed across SDKs ({', '.join(failed_sdks)}), "
                f"while other providers ({', '.join(passed_providers)}) succeeded. "
                "Diagnosis: Upstream model provider outage, quota exhaustion, or Key Vault credential failure."
            ),
            affected_sdks=failed_sdks,
            affected_providers=dead_providers,
        )

    # Case 3: Single SDK Regression
    if len(failed_sdks) == 1:
        bad_sdk = failed_sdks[0]
        bad_prov = failed_providers[0] if failed_providers else "unknown"
        return TriageVerdict(
            category="SDK_REGRESSION",
            severity="warning",
            diagnosis=(
                f"SDK '{bad_sdk}' failed against provider '{bad_prov}', while other SDKs succeeded. "
                f"Diagnosis: Language-specific regression in sdks/{bad_sdk} (wire serialization, header handling, or client bug)."
            ),
            affected_sdks=[bad_sdk],
            affected_providers=failed_providers,
        )

    # Case 4: Multiple scattered failures
    return TriageVerdict(
        category="PARTIAL_DEGRADATION",
        severity="warning",
        diagnosis=(
            f"{len(failed_sdks)} SDKs ({', '.join(failed_sdks)}) reported failures across {len(failed_providers)} providers. "
            "Diagnosis: Partial network degradation or multiple isolated service issues."
        ),
        affected_sdks=failed_sdks,
        affected_providers=failed_providers,
    )


def build_report_data(
    results: List[Dict[str, Any]],
    preflight: Optional[Dict[str, Any]] = None,
    history_file: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compile comprehensive report data dictionary."""
    results_sorted = sorted(results, key=lambda x: x.get("sdk", ""))

    total = len(results_sorted)
    passed = sum(1 for r in results_sorted if r.get("status") == "passed")
    failed = sum(1 for r in results_sorted if r.get("status") == "failed")
    skipped = sum(1 for r in results_sorted if r.get("status") == "skipped")

    latencies = [r.get("latency_ms", 0) for r in results_sorted if r.get("latency_ms", 0) > 0]
    avg_latency = int(sum(latencies) / len(latencies)) if latencies else 0

    costs = [r.get("cost_usd", 0.0) for r in results_sorted if r.get("cost_usd")]
    total_cost = sum(costs)

    providers = sorted(list({r.get("provider") for r in results_sorted if r.get("provider")}))

    triage = evaluate_triage(results_sorted)

    # Read existing 30-day history if available
    history: List[Dict[str, Any]] = []
    if history_file and history_file.exists():
        try:
            history = json.loads(history_file.read_text(encoding="utf-8"))
        except Exception:
            history = []

    # Append current run to history
    today_str = time.strftime("%Y-%m-%d", time.gmtime())
    current_status = "passed" if failed == 0 else ("outage" if failed >= 3 else "degraded")
    # Replace today's entry if already present, or append
    history = [h for h in history if h.get("date") != today_str]
    history.append({
        "date": today_str,
        "status": current_status,
        "passed": passed,
        "failed": failed,
        "total": total,
    })
    history = history[-30:]  # Keep rolling 30 days

    version = results_sorted[0].get("version", "3.1.2") if results_sorted else "3.1.2"

    return {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "version": version,
        "summary": {
            "total": total,
            "passed": passed,
            "failed": failed,
            "skipped": skipped,
            "avg_latency_ms": avg_latency,
            "total_cost_usd": round(total_cost, 6),
            "providers_count": len(providers),
            "providers": providers,
        },
        "preflight": preflight or {},
        "triage": asdict(triage),
        "results": results_sorted,
        "history": history,
    }


def render_html_dashboard(report_data: Dict[str, Any], output_path: Path) -> None:
    """Render dist/index.html using resources/sentinel/template.html."""
    template_file = ROOT / "resources" / "sentinel" / "template.html"
    if not template_file.exists():
        raise FileNotFoundError(f"Template file {template_file} not found")

    template_content = template_file.read_text(encoding="utf-8")
    data_json = json.dumps(report_data)
    rendered = template_content.replace("/*REPORT_DATA_PLACEHOLDER*/{}", data_json)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(rendered, encoding="utf-8")


def render_csv_report(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Render flat tabular CSV for audit archive."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "sdk", "version", "status", "provider", "model",
        "endpoint", "latency_ms", "cost_usd", "cost_status",
        "request_id", "timestamp", "error"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in results:
            writer.writerow(r)


def generate_step_summary_md(report_data: Dict[str, Any]) -> str:
    """Format GitHub Step Summary markdown."""
    summary = report_data["summary"]
    triage = report_data["triage"]
    preflight = report_data.get("preflight", {})

    status_badge = "🟢 **ALL 10 SDKs OPERATIONAL**" if summary["failed"] == 0 else f"🔴 **{summary['failed']} SDK/PROVIDER FAILURES**"

    lines = [
        "## nRouter SDK & Provider Health Sentinel Report",
        f"**Posture**: {status_badge} &bull; **Time**: `{report_data['timestamp']}` &bull; **Version**: `v{report_data['version']}`",
        "",
        "### Executive Summary",
        f"- **SDK Pass Rate**: **{summary['passed']}/{summary['total']}** ({int((summary['passed']/max(summary['total'], 1))*100)}%)",
        f"- **Tested Providers**: {', '.join(summary['providers']) or 'None'}",
        f"- **Average Latency**: `{summary['avg_latency_ms']} ms`",
        f"- **Canary Spend**: `${summary['total_cost_usd']:.5f}` (Cap: `$1.00 / day`)",
        f"- **Catalog Models Available**: `{preflight.get('models_count', 'N/A')}`",
        "",
    ]

    if triage["category"] != "ALL_OPERATIONAL":
        lines.extend([
            f"> [!WARNING]",
            f"> **Sentinel Failure Triage: {triage['category']}**",
            f"> {triage['diagnosis']}",
            "",
        ])

    lines.extend([
        "### SDK & Provider Canary Results",
        "| SDK | Provider | Tested Model | Endpoint | Status | Latency | Request ID |",
        "|:---|:---|:---|:---|:---:|:---:|:---|",
    ])

    for r in report_data["results"]:
        status_icon = "✅ Pass" if r.get("status") == "passed" else ("❌ FAIL" if r.get("status") == "failed" else "⏸ Skip")
        req_id = r.get("request_id") or "N/A"
        trace_link = f"[`{req_id[:14]}...`](https://app.nrouter.ai/traces/{req_id})" if req_id != "N/A" else "N/A"
        lines.append(
            f"| **{r.get('sdk')}** | {r.get('provider')} | `{r.get('model')}` | `{r.get('endpoint')}` | {status_icon} | `{r.get('latency_ms')} ms` | {trace_link} |"
        )

    return "\n".join(lines)


def self_test() -> int:
    """Verify aggregator, failure triage heuristics, CSV/JSON outputs, and HTML rendering."""
    print("======================================================================")
    print("Sentinel Aggregator & Triage Engine Self-Test")
    print("======================================================================")
    fails = 0

    def assert_true(label: str, cond: bool) -> None:
        nonlocal fails
        if cond:
            print(f"  ok   {label}")
        else:
            print(f"  FAIL {label}")
            fails += 1

    # Fixture 1: All 10 Passing
    all_pass = [
        {"sdk": s, "version": "3.1.2", "status": "passed", "provider": "openai" if i % 2 == 0 else "anthropic",
         "model": "m", "endpoint": "/v1/chat", "latency_ms": 100 + i, "cost_usd": 0.0001, "request_id": f"req-{i}"}
        for i, s in enumerate(["android", "dart", "go", "java", "js", "kotlin", "python", "r", "rust", "swift"])
    ]
    t1 = evaluate_triage(all_pass)
    assert_true("triage reports ALL_OPERATIONAL on all pass", t1.category == "ALL_OPERATIONAL")

    # Fixture 2: Single SDK failure -> SDK_REGRESSION
    single_fail = [dict(r) for r in all_pass]
    single_fail[6]["status"] = "failed"  # python fails
    t2 = evaluate_triage(single_fail)
    assert_true("triage reports SDK_REGRESSION when 1 SDK fails", t2.category == "SDK_REGRESSION")
    assert_true("triage identifies affected SDK", t2.affected_sdks == ["python"])

    # Fixture 3: Provider outage -> PROVIDER_OUTAGE_OR_QUOTA
    prov_fail = [dict(r) for r in all_pass]
    for r in prov_fail:
        if r["provider"] == "anthropic":
            r["status"] = "failed"
    t3 = evaluate_triage(prov_fail)
    assert_true("triage reports PROVIDER_OUTAGE when all calls to a provider fail", t3.category == "PROVIDER_OUTAGE_OR_QUOTA")
    assert_true("triage identifies affected provider", "anthropic" in t3.affected_providers)

    # Fixture 4: All SDKs fail -> GATEWAY_OR_AUTH_DOWN
    all_fail = [dict(r) for r in all_pass]
    for r in all_fail:
        r["status"] = "failed"
    t4 = evaluate_triage(all_fail)
    assert_true("triage reports GATEWAY_OR_AUTH_DOWN when all SDKs fail", t4.category == "GATEWAY_OR_AUTH_DOWN")

    # Fixture 5: HTML dashboard generation
    report_data = build_report_data(all_pass)
    test_out = ROOT / ".scratch" / "test_sentinel_dist" / "index.html"
    render_html_dashboard(report_data, test_out)
    assert_true("renders dashboard HTML file", test_out.exists())
    assert_true("dashboard includes version", "3.1.2" in test_out.read_text(encoding="utf-8"))

    # Fixture 6: Step summary markdown
    summary_md = generate_step_summary_md(report_data)
    assert_true("generates markdown summary", "ALL 10 SDKs OPERATIONAL" in summary_md and "| **python** |" in summary_md)

    if fails == 0:
        print("\nAll aggregator & triage self-tests PASSED.")
        return 0
    else:
        print(f"\n{fails} self-test assertion(s) FAILED.")
        return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Aggregate Sentinel Canary results and generate dashboard")
    parser.add_argument("--self-test", action="store_true", help="Run aggregator self-test")
    parser.add_argument("--fixture", action="store_true", help="Use synthetic fixture data")
    parser.add_argument("--results-dir", type=str, help="Directory containing sentinel-result-*.json files")
    parser.add_argument("--preflight-file", type=str, help="Path to sentinel-preflight.json")
    parser.add_argument("--output-dir", type=str, default="./dist", help="Directory to write reports & dashboard")
    parser.add_argument("--history-file", type=str, help="Path to existing history.json")
    parser.add_argument("--step-summary", action="store_true", help="Append markdown to $GITHUB_STEP_SUMMARY")

    args = parser.parse_args()

    if args.self_test:
        return self_test()

    results: List[Dict[str, Any]] = []
    preflight: Dict[str, Any] = {}

    if args.fixture:
        all_sdks = ["android", "dart", "go", "java", "js", "kotlin", "python", "r", "rust", "swift"]
        providers = ["openai", "anthropic", "qwen"]
        for i, s in enumerate(all_sdks):
            p = providers[i % len(providers)]
            m = "claude-haiku-4-5-20251001" if p == "anthropic" else ("qwen-turbo" if p == "qwen" else "openai/gpt-4o-mini")
            ep = "/v1/messages" if p == "anthropic" else "/v1/chat/completions"
            results.append({
                "sdk": s,
                "version": "3.1.2",
                "status": "passed",
                "provider": p,
                "model": m,
                "endpoint": ep,
                "latency_ms": 115 + (i * 12),
                "cost_usd": 0.00011,
                "cost_status": "exact",
                "request_id": f"req-fixture-{s}-001",
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "error": None,
            })
        preflight = {"catalog_status": "ok", "models_count": 84, "latency_ms": 42, "conformance_passed": True}
    elif args.results_dir:
        res_dir = Path(args.results_dir)
        if not res_dir.exists():
            print(f"Error: results directory {res_dir} does not exist", file=sys.stderr)
            return 1

        for json_path in res_dir.glob("sentinel-result-*.json"):
            try:
                data = json.loads(json_path.read_text(encoding="utf-8"))
                results.append(data)
            except Exception as e:
                print(f"Warning: failed to read {json_path}: {e}", file=sys.stderr)

        if args.preflight_file and Path(args.preflight_file).exists():
            try:
                preflight = json.loads(Path(args.preflight_file).read_text(encoding="utf-8"))
            except Exception as e:
                print(f"Warning: failed to read preflight file: {e}", file=sys.stderr)
    else:
        parser.print_help()
        return 0

    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    hist_file = Path(args.history_file) if args.history_file else out_dir / "history.json"
    report_data = build_report_data(results, preflight=preflight, history_file=hist_file)

    # 1. Output machine-readable JSON & CSV reports
    (out_dir / "sentinel-report.json").write_text(json.dumps(report_data, indent=2), encoding="utf-8")
    (out_dir / "status.json").write_text(json.dumps({
        "status": report_data["triage"]["category"],
        "passed": report_data["summary"]["passed"],
        "total": report_data["summary"]["total"],
        "timestamp": report_data["timestamp"],
        "version": report_data["version"],
    }, indent=2), encoding="utf-8")
    (out_dir / "history.json").write_text(json.dumps(report_data["history"], indent=2), encoding="utf-8")
    render_csv_report(results, out_dir / "sentinel-report.csv")

    # 2. Render GitHub Pages dashboard
    render_html_dashboard(report_data, out_dir / "index.html")
    print(f"Dashboard and reports generated at {out_dir}")

    # 3. Output Step Summary
    summary_md = generate_step_summary_md(report_data)
    if args.step_summary or "GITHUB_STEP_SUMMARY" in os.environ:
        step_summary_path = os.getenv("GITHUB_STEP_SUMMARY")
        if step_summary_path:
            with open(step_summary_path, "a", encoding="utf-8") as f:
                f.write("\n" + summary_md + "\n")
            print("Appended markdown summary to $GITHUB_STEP_SUMMARY")
        else:
            print("\n" + summary_md)
    else:
        print("\nSummary:")
        print(f"  Passed: {report_data['summary']['passed']}/{report_data['summary']['total']}")
        print(f"  Triage: {report_data['triage']['category']}")

    return 0 if report_data["summary"]["failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
