#!/usr/bin/env python3
"""
================================================================================
 R02-T001  |  Parse the entries: Cryptocurrency  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T001 (1 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/1
 Branch    : student/e26b07f0820/R02-T001

 WHAT THIS SCRIPT DOES
 ----------------------
 Parses the public-apis README.md and extracts structured metadata for three
 assigned entries in the Cryptocurrency section:
   - Coinlayer  (https://coinlayer.com)
   - 0x         (https://docs.0x.org/)
   - 1inch      (https://business.1inch.com/portal/documentation)

 For each entry the script extracts:
   - Display name        (e.g. "Coinlayer")
   - URL                 (preserving query params AND fragments)
   - Category            (nearest ### heading above the entry)
   - Description, Auth, HTTPS, CORS fields
   - Source line number  (so reviewers can pinpoint the exact README line)

 KEY DESIGN DECISIONS
 ---------------------
 1. Fenced-code blocks (``` or ~~~) are skipped — fake/example links inside
    them must NOT be harvested as real entries.
 2. URL fragments (e.g. #section) are preserved; they can be meaningful.
 3. Parsing is name-exact (case-insensitive) — no fuzzy matching.
 4. All results are saved to work/R02-T001/results.json for audit.

 USAGE
 -----
   python3 r02-t001.py               # run against real README.md
   python3 r02-t001.py --self-test   # run offline fixture tests (no network)

 DONE WHEN (from issue #1)
 --------------------------
   ✓ Fenced-code fake link is ignored
   ✓ URL containing a fragment is preserved
   ✓ Each selected real entry maps back to its source line
   ✓ --self-test mode exits non-zero when an assertion fails
================================================================================
"""

import re
import sys
import os
import json

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T001")

# Entries assigned to this task
TARGET_ENTRIES = ["Coinlayer", "0x", "1inch"]
TARGET_URLS = [
    "https://coinlayer.com",
    "https://docs.0x.org/",
    "https://business.1inch.com/portal/documentation",
]


def parse_readme_table_row(line: str, line_num: int) -> dict | None:
    """Parse a markdown table row for the public-apis catalogue format.

    Format: | [Name](URL) | Description | Auth | HTTPS | CORS |
    Returns None if the line is not a data row.
    """
    line = line.rstrip()
    # Must start and end with |
    if not (line.startswith("|") and line.endswith("|")):
        return None
    # Split cells
    cells = [c.strip() for c in line.split("|")]
    cells = [c for c in cells if c != ""]  # remove empty edge cells
    if len(cells) < 4:
        return None

    # First cell must be a markdown link [Name](URL)
    link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", cells[0])
    if not link_match:
        return None

    name = link_match.group(1)
    url = link_match.group(2)
    description = cells[1] if len(cells) > 1 else ""
    auth = cells[2] if len(cells) > 2 else ""
    https = cells[3] if len(cells) > 3 else ""
    cors = cells[4] if len(cells) > 4 else ""

    return {
        "line_number": line_num,
        "name": name,
        "url": url,
        "description": description,
        "auth": auth,
        "https": https,
        "cors": cors,
    }


def find_category_for_line(lines: list, target_line: int) -> str:
    """Walk backwards from target_line to find the nearest ### heading."""
    for i in range(target_line - 2, -1, -1):
        if lines[i].startswith("### "):
            return lines[i][4:].strip()
    return "Unknown"


def parse_entries(readme_path: str = README_PATH) -> list[dict]:
    """Parse the README and return all entries for TARGET_ENTRIES."""
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    in_code_block = False

    for idx, line in enumerate(lines, start=1):
        # Track fenced code blocks — ignore links inside them
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        entry = parse_readme_table_row(line, idx)
        if entry is None:
            continue

        # Check if entry name matches any target
        for target in TARGET_ENTRIES:
            if entry["name"].lower() == target.lower():
                entry["category"] = find_category_for_line(lines, idx)
                results.append(entry)
                break

    return results


def run(readme_path: str = README_PATH) -> None:
    """Main entry point: parse and print results."""
    entries = parse_entries(readme_path)
    print("=" * 60)
    print("R02-T001: Parsed Cryptocurrency Entries")
    print("=" * 60)
    for e in entries:
        print(f"\nLine {e['line_number']}: [{e['name']}]({e['url']})")
        print(f"  Category   : {e['category']}")
        print(f"  Description: {e['description']}")
        print(f"  Auth       : {e['auth']}")
        print(f"  HTTPS      : {e['https']}")
        print(f"  CORS       : {e['cors']}")

    # Save results to work dir
    os.makedirs(WORK_DIR, exist_ok=True)
    output_path = os.path.join(WORK_DIR, "results.json")
    with open(output_path, "w") as f:
        json.dump(entries, f, indent=2)
    print(f"\nResults saved to {output_path}")
    return entries


# ---------------------------------------------------------------------------
# Self-test mode
# ---------------------------------------------------------------------------

FIXTURE_REAL = """\
### Cryptocurrency

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [Coinlayer](https://coinlayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers) | Real-time Crypto Currency Exchange Rates | `apiKey` | Yes | Unknown |
| [0x](https://docs.0x.org/) | API for querying token and pool stats across various liquidity pools | No | Yes | Yes |
| [1inch](https://business.1inch.com/portal/documentation) | API for querying decentralize exchange | `apiKey` | Yes | Unknown |
"""

FIXTURE_WITH_CODE_BLOCK = """\
### Cryptocurrency

```
| [FakeEntry](https://fake.example.com) | Should be ignored | No | Yes | Yes |
```

| [0x](https://docs.0x.org/) | Real entry | No | Yes | Yes |
"""

FIXTURE_WITH_FRAGMENT = """\
### Cryptocurrency

| [FragAPI](https://example.com/docs#section-1) | Has fragment | No | Yes | Yes |
"""


def _parse_fixture(text: str) -> list[dict]:
    """Parse a string fixture as if it were a README."""
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        name = f.name
    # Temporarily override TARGET_ENTRIES to find any entry
    global TARGET_ENTRIES
    old = TARGET_ENTRIES[:]
    TARGET_ENTRIES = ["Coinlayer", "0x", "1inch", "FragAPI"]
    try:
        result = parse_entries(name)
    finally:
        TARGET_ENTRIES = old
        os.unlink(name)
    return result


def self_test() -> None:
    """Run offline self-tests. Exit non-zero on failure."""
    failures = []

    # Test 1: Real entries are found with correct line numbers and category
    entries = _parse_fixture(FIXTURE_REAL)
    names = [e["name"] for e in entries]
    if "Coinlayer" not in names:
        failures.append("FAIL: Coinlayer not found in real fixture")
    if "0x" not in names:
        failures.append("FAIL: 0x not found in real fixture")
    if "1inch" not in names:
        failures.append("FAIL: 1inch not found in real fixture")
    for e in entries:
        if e["category"] != "Cryptocurrency":
            failures.append(f"FAIL: Expected category 'Cryptocurrency' got '{e['category']}'")
        if e["line_number"] < 1:
            failures.append(f"FAIL: line_number must be >= 1, got {e['line_number']}")

    # Test 2: Fenced-code fake link is ignored
    entries2 = _parse_fixture(FIXTURE_WITH_CODE_BLOCK)
    names2 = [e["name"] for e in entries2]
    if "FakeEntry" in names2:
        failures.append("FAIL: FakeEntry inside code block should be ignored")
    if "0x" not in names2:
        failures.append("FAIL: 0x outside code block should be found")

    # Test 3: URL containing a fragment is preserved
    global TARGET_ENTRIES
    old = TARGET_ENTRIES[:]
    TARGET_ENTRIES = ["FragAPI"]
    entries3 = _parse_fixture(FIXTURE_WITH_FRAGMENT)
    TARGET_ENTRIES = old
    if entries3:
        frag_url = entries3[0]["url"]
        if "#section-1" not in frag_url:
            failures.append(f"FAIL: Fragment not preserved in URL: {frag_url}")
    else:
        failures.append("FAIL: FragAPI not found in fragment fixture")

    # Report
    if failures:
        print("SELF-TEST FAILURES:")
        for f in failures:
            print(f"  {f}")
        sys.exit(1)
    else:
        print("All R02-T001 self-tests PASSED.")
        # Save test evidence
        os.makedirs(WORK_DIR, exist_ok=True)
        evidence = {
            "tool": "r02-t001.py",
            "tests": [
                {"name": "real_entries_found", "status": "PASS"},
                {"name": "fenced_code_link_ignored", "status": "PASS"},
                {"name": "url_fragment_preserved", "status": "PASS"},
            ],
        }
        with open(os.path.join(WORK_DIR, "self_test_evidence.json"), "w") as f:
            json.dump(evidence, f, indent=2)


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
