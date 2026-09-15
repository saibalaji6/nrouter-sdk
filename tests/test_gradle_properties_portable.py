"""Committed Gradle configuration must build on any machine.

A committed `gradle.properties` is read on every machine that builds the SDK,
so a machine-specific JDK location in it becomes everyone's configuration. The
Android SDK once named two macOS Homebrew JDKs in
`org.gradle.java.installations.paths`, and a Windows build then warned about
Java installations that cannot exist there.

Where a JDK lives is a property of the machine, not of the project. The local
test runner supplies it at invocation time (`-Porg.gradle.java.installations.paths=...`),
and only for directories that exist.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MACHINE_KEYS = ("org.gradle.java.installations.paths", "org.gradle.java.home")
# Any absolute path in a value: a POSIX root or a Windows drive. Not a list of
# known prefixes, which /nix/store, /snap or /var/lib would walk past.
ABSOLUTE_PATH = re.compile(r"(^|[=,;\s])(/[^\s/]|[A-Za-z]:[\\/])")


def _tracked_gradle_properties() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "*gradle.properties"],
        cwd=ROOT, check=True, capture_output=True, text=True,
    ).stdout.split()
    return [ROOT / p for p in out]


def test_there_are_gradle_properties_to_check() -> None:
    names = {p.relative_to(ROOT).as_posix() for p in _tracked_gradle_properties()}
    assert {"sdks/kotlin/gradle.properties", "sdks/android/gradle.properties"} <= names


def test_no_committed_gradle_properties_names_a_machine_jdk() -> None:
    files = _tracked_gradle_properties()
    # Checked here too, not only in the test above: run alone, an empty list
    # would make this invariant pass having inspected nothing.
    assert files, "no tracked gradle.properties found; the check below would be vacuous"
    offenders = []
    for path in files:
        for number, line in enumerate(path.read_text().splitlines(), 1):
            stripped = line.strip()
            if not stripped or stripped.startswith(("#", "!")):
                continue
            key, _, value = stripped.partition("=")
            if key.strip() in MACHINE_KEYS or ABSOLUTE_PATH.search(value):
                offenders.append(f"{path.relative_to(ROOT)}:{number}: {stripped}")
    assert not offenders, "machine-specific JDK configuration is committed:\n" + "\n".join(offenders)


def test_local_runner_supplies_jdk_paths_to_both_gradle_lanes() -> None:
    script = (ROOT / "scripts" / "test-all.sh").read_text()
    for lane in ("sdks/kotlin' && ./gradlew", "sdks/android' && ./gradlew"):
        line = next((l for l in script.splitlines() if lane in l), None)
        assert line is not None, f"lane not found: {lane}"
        assert "$GRADLE_JDK_ARGS" in line, f"lane does not pass the machine's JDKs: {line.strip()}"
