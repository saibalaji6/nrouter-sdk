#!/usr/bin/env bash
set -euo pipefail

cd "$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

SPEC="spec/nrouter-sdk-spec.json"
README="README.md"

if [ ! -f "$SPEC" ]; then
  echo "FAIL: spec file $SPEC not found" >&2
  exit 1
fi

if [ ! -f "$README" ]; then
  echo "FAIL: README file $README not found" >&2
  exit 1
fi

ERROR_CODES=$(python3 -c '
import json
with open("spec/nrouter-sdk-spec.json") as f:
    spec = json.load(f)
for code in spec.get("errors", {}).keys():
    print(code)
')

HEADERS=$(python3 -c '
import json
with open("spec/nrouter-sdk-spec.json") as f:
    spec = json.load(f)
for h in spec.get("response_headers", {}).keys():
    if h.startswith("x-nr-"):
        print(h)
')

EXPECTED_CODE_COUNT=$(python3 -c '
import json
with open("spec/nrouter-sdk-spec.json") as f:
    spec = json.load(f)
print(len(spec.get("errors", {})))
')

fails=0

# 1. Check for error code count differences
count_check=$(python3 -c '
import json, re, sys

with open("spec/nrouter-sdk-spec.json") as f:
    spec = json.load(f)
expected_count = len(spec.get("errors", {}))

with open("README.md") as f:
    readme = f.read()

words_to_num = {
    "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
    "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
    "eleven": 11, "twelve": 12
}

stale_counts = []
for match in re.finditer(r"\b(\d+)\s+(?:codes|classed conditions)\b", readme, re.I):
    count = int(match.group(1))
    if count != expected_count:
        stale_counts.append(f"{match.group(0)} (stated {count} vs expected {expected_count})")

for match in re.finditer(r"\b(\w+)\s+typed\s+(?:gateway\s+)?errors?\b", readme, re.I):
    word = match.group(1).lower()
    val = int(word) if word.isdigit() else words_to_num.get(word)
    if val is not None and val != expected_count:
        stale_counts.append(f"{match.group(0)} (stated {val} vs expected {expected_count})")

if stale_counts:
    for sc in stale_counts:
        print(f"FAIL: README states differing code count: {sc}")
    sys.exit(1)
' 2>&1 || true)

if [ -n "$count_check" ]; then
  echo "$count_check" >&2
  fails=$((fails + 1))
fi

# 2. Check that every error code in spec is in README
for code in $ERROR_CODES; do
  if ! grep -F -q "$code" "$README"; then
    echo "FAIL: Error code '$code' from spec is missing from $README" >&2
    fails=$((fails + 1))
  fi
done

# 3. Check that every x-nr-* header in spec is in README
for header in $HEADERS; do
  if ! grep -F -q "$header" "$README"; then
    echo "FAIL: Header '$header' from spec is missing from $README" >&2
    fails=$((fails + 1))
  fi
done

if [ "$fails" -gt 0 ]; then
  echo "README spec parity check: FAILED ($fails errors)" >&2
  exit 1
fi

echo "README spec parity check: PASS"
