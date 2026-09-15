#!/usr/bin/env python3
"""Run a tiny, date-rotated nRouter text-provider canary.

The script deliberately uses only the standard library. It discovers callable
models from /v1/models rather than maintaining a stale model list in this
public repository.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path
from typing import Any


ROUTES = ("/v1/messages", "/v1/chat/completions", "/v1/responses")


def provider_label(model: dict[str, Any]) -> str:
    """Use catalogue metadata when available, otherwise avoid guessing."""
    return str(model.get("provider") or model.get("owned_by") or model.get("maker") or "catalogue")


def approved_models(route: str) -> tuple[str, ...]:
    """Read the operator-approved, low-cost candidates for one route."""
    names = {
        "/v1/messages": "NROUTER_PROVIDER_SENTINEL_MESSAGES_MODELS",
        "/v1/chat/completions": "NROUTER_PROVIDER_SENTINEL_CHAT_MODELS",
        "/v1/responses": "NROUTER_PROVIDER_SENTINEL_RESPONSES_MODELS",
    }
    return tuple(model.strip() for model in os.getenv(names[route], "").split(",") if model.strip())


def choose(
    catalogue: list[dict[str, Any]], route: str, run_date: str, allowed: tuple[str, ...]
) -> dict[str, Any] | None:
    candidates = sorted(
        (item for item in catalogue if item.get("id") in allowed and route in item.get("nrouter_endpoints", [])),
        key=lambda item: str(item.get("id", "")),
    )
    if not candidates:
        return None
    index = int(hashlib.sha256(f"{run_date}:{route}".encode()).hexdigest(), 16) % len(candidates)
    return candidates[index]


def payload(route: str, model: str) -> dict[str, Any]:
    if route == "/v1/messages":
        return {"model": model, "max_tokens": 2, "messages": [{"role": "user", "content": "OK"}]}
    if route == "/v1/chat/completions":
        return {"model": model, "max_tokens": 2, "messages": [{"role": "user", "content": "OK"}]}
    # OpenAI's Responses API rejects the two-token minimum used by the other text wires.
    return {"model": model, "input": "OK", "max_output_tokens": 16}


def call(base_url: str, api_key: str, route: str, body: dict[str, Any]) -> tuple[int, dict[str, str], str]:
    path = route.removeprefix("/v1")
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}{path}",
        data=json.dumps(body).encode(),
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            response.read()
            return response.status, dict(response.headers.items()), ""
    except urllib.error.HTTPError as error:
        return error.code, dict(error.headers.items()), f"HTTP {error.code}"
    except urllib.error.URLError as error:
        return 0, {}, f"transport: {error.reason}"


def run(base_url: str, api_key: str, run_date: str) -> list[dict[str, Any]]:
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/models", headers={"Authorization": f"Bearer {api_key}"}
    )
    with urllib.request.urlopen(request, timeout=45) as response:
        document = json.load(response)
    catalogue = document.get("data")
    if not isinstance(catalogue, list) or not catalogue:
        raise RuntimeError("GET /v1/models returned no models")

    results: list[dict[str, Any]] = []
    for route in ROUTES:
        selected = choose(catalogue, route, run_date, approved_models(route))
        if selected is None:
            results.append({"route": route, "result": "skipped", "reason": "no advertised model"})
            continue
        started = time.monotonic()
        status, headers, error = call(base_url, api_key, route, payload(route, str(selected["id"])))
        results.append(
            {
                "provider": provider_label(selected),
                "model": selected["id"],
                "route": route,
                "result": "passed" if 200 <= status < 300 else "failed",
                "status": status,
                "latency_ms": round((time.monotonic() - started) * 1000),
                "request_id": headers.get("x-nr-request-id", ""),
                "error": error,
            }
        )
    return results


def write_summary(results: list[dict[str, Any]], run_date: str) -> None:
    lines = [
        "# nRouter provider sentinel",
        "",
        f"Rotation date: {run_date}",
        "",
        "| Provider | Model | Endpoint | Result | Status | Latency | Request ID |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for result in results:
        lines.append(
            "| {provider} | {model} | {route} | {result} | {status} | {latency} ms | {request_id} |".format(
                provider=result.get("provider", "-"),
                model=result.get("model", "-"),
                route=result["route"],
                result=result["result"],
                status=result.get("status", "-"),
                latency=result.get("latency_ms", "-"),
                request_id=result.get("request_id", "-"),
            )
        )
    summary = "\n".join(lines) + "\n"
    print(summary)
    if github_summary := os.getenv("GITHUB_STEP_SUMMARY"):
        Path(github_summary).write_text(summary, encoding="utf-8")


def self_test() -> None:
    catalogue = [
        {"id": "b", "nrouter_endpoints": ["/v1/chat/completions"]},
        {"id": "a", "nrouter_endpoints": ["/v1/chat/completions"]},
        {"id": "c", "nrouter_endpoints": ["/v1/messages"]},
    ]
    assert choose(catalogue, "/v1/chat/completions", "2026-09-14", ("a", "b"))["id"] in {"a", "b"}
    assert choose(catalogue, "/v1/responses", "2026-09-14", ("a",)) is None
    responses_payload = payload("/v1/responses", "model")
    assert responses_payload["input"] == "OK"
    assert responses_payload["max_output_tokens"] == 16


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", default="provider-sentinel.json")
    parser.add_argument("--date", default=date.today().isoformat())
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return 0

    api_key = os.getenv("NROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("NROUTER_API_KEY is required for a billed provider canary")
    results = run(os.getenv("NROUTER_BASE_URL", "https://api.nrouter.ai/v1"), api_key, args.date)
    Path(args.output).write_text(json.dumps({"date": args.date, "results": results}, indent=2) + "\n", encoding="utf-8")
    write_summary(results, args.date)
    return 1 if any(result["result"] == "failed" for result in results) else 0


if __name__ == "__main__":
    sys.exit(main())
