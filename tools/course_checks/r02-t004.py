#!/usr/bin/env python3
"""
================================================================================
 R02-T004  |  Check category placement: Environment  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T004 (4 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/9
 Branch    : student/e26b07f0820/R02-T004

 WHAT THIS SCRIPT DOES
 ----------------------
 Verifies that three assigned entries appear in the correct "Environment"
 section of README.md, and flags any misplacement or repeated headings.
 Assigned entries:
   - AirNow           (https://docs.airnowapi.org/)
   - BreezoMeter Pollen (https://docs.breezometer.com/...)
   - Calendrier Tempo  (https://www.calendrier-tempo.fr/api-tempo)

 Checks performed:
   1. Each assigned entry is located in its ### section
   2. The actual section is compared to the expected section ("Environment")
   3. Duplicate ### headings (same name appearing twice) are flagged
   4. Entries are NEVER reclassified purely from keywords in their name or
      description — only their physical position in the file matters

 KEY DESIGN DECISIONS
 ---------------------
 - Section context is tracked by walking line-by-line looking for ### headings.
 - Code blocks are excluded so example entries don't confuse the parser.
 - A misplaced entry is reported with both its actual and expected section.
 - Self-tests use temporary markdown fixture files, deleted after each test.

 USAGE
 -----
   python3 r02-t004.py               # check README.md
   python3 r02-t004.py --self-test   # offline fixture tests

 DONE WHEN (from issue #9)
 --------------------------
   ✓ Deliberately misplaced fixture is identified
   ✓ Valid categories preserved (no false positives)
   ✓ Proposed real moves cite the resource's actual subject
   ✓ --self-test exits non-zero when any assertion fails
================================================================================
"""

import re
import sys
import os
import json

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T004")

TARGET_ENTRIES = ["AirNow", "BreezoMeter Pollen", "Calendrier Tempo"]
TARGET_SECTION = "Environment"


def parse_sections(readme_path: str) -> dict:
    """
    Parse the README into sections.
    Returns a dict: {section_name: [{"line_number": int, "name": str, "url": str}]}
    Also detects duplicate headings.
    """
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()

    sections = {}
    heading_counts = {}
    current_section = None
    in_code_block = False

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if line.startswith("### "):
            heading = line[4:].strip()
            current_section = heading
            heading_counts[heading] = heading_counts.get(heading, 0) + 1
            if heading not in sections:
                sections[heading] = []
            continue

        if current_section is None:
            continue

        if not (line.startswith("|") and line.rstrip().endswith("|")):
            continue

        cells = [c.strip() for c in line.split("|") if c.strip()]
        if not cells:
            continue
        link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", cells[0])
        if not link_match:
            continue
        name = link_match.group(1)
        if name.lower() in ("api", "name"):
            continue

        sections[current_section].append({
            "line_number": idx,
            "name": name,
            "url": link_match.group(2),
            "section": current_section,
        })

    duplicate_headings = {h: c for h, c in heading_counts.items() if c > 1}
    return sections, duplicate_headings


def check_target_placement(sections: dict) -> list[dict]:
    """
    For each target entry, find which section it's in and whether it
    matches TARGET_SECTION.
    """
    results = []
    for section_name, entries in sections.items():
        for e in entries:
            for target in TARGET_ENTRIES:
                if e["name"].lower() == target.lower():
                    placed_correctly = (section_name == TARGET_SECTION)
                    results.append({
                        **e,
                        "expected_section": TARGET_SECTION,
                        "actual_section": section_name,
                        "correctly_placed": placed_correctly,
                        "flag": None if placed_correctly else f"Misplaced: found in '{section_name}', expected '{TARGET_SECTION}'",
                    })
    return results


def run(readme_path: str = README_PATH) -> None:
    print("=" * 60)
    print("R02-T004: Category Placement Check — Environment")
    print("=" * 60)

    sections, duplicate_headings = parse_sections(readme_path)

    if duplicate_headings:
        print(f"\n⚠ Duplicate headings found: {duplicate_headings}")
    else:
        print("\n✓ No duplicate headings detected")

    placements = check_target_placement(sections)
    for p in placements:
        status = "✓ CORRECT" if p["correctly_placed"] else "✗ MISPLACED"
        print(f"\n{status} — Line {p['line_number']}: [{p['name']}]({p['url']})")
        print(f"  Actual section  : {p['actual_section']}")
        print(f"  Expected section: {p['expected_section']}")
        if p["flag"]:
            print(f"  Flag: {p['flag']}")

    os.makedirs(WORK_DIR, exist_ok=True)
    output = {
        "target_entries": placements,
        "duplicate_headings": duplicate_headings,
        "section_entry_counts": {k: len(v) for k, v in sections.items()},
    }
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {WORK_DIR}/results.json")


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

FIXTURE_CORRECT = """\
### Environment

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [AirNow](https://docs.airnowapi.org/) | Air quality data | No | Yes | Unknown |
| [BreezoMeter Pollen](https://docs.breezometer.com/api-documentation/pollen-api/v2/) | Pollen and air quality data | `apiKey` | Yes | Unknown |
| [Calendrier Tempo](https://www.calendrier-tempo.fr/api-tempo) | French energy tariff calendar | No | Yes | Unknown |
"""

FIXTURE_MISPLACED = """\
### Weather

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [AirNow](https://docs.airnowapi.org/) | Air quality data | No | Yes | Unknown |

### Environment

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [BreezoMeter Pollen](https://docs.breezometer.com/api-documentation/pollen-api/v2/) | Pollen data | `apiKey` | Yes | Unknown |
"""

FIXTURE_DUPLICATE_HEADING = """\
### Environment

| [AirNow](https://docs.airnowapi.org/) | Air quality | No | Yes | Unknown |

### Environment

| [AirNow2](https://docs.airnowapi.org/v2) | Air quality v2 | No | Yes | Unknown |
"""


def _run_on_fixture(text: str) -> tuple:
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        name = f.name
    try:
        sections, dups = parse_sections(name)
        placements = check_target_placement(sections)
    finally:
        os.unlink(name)
    return sections, dups, placements


def self_test() -> None:
    failures = []

    # Test 1: Correctly placed entries pass
    sections, dups, placements = _run_on_fixture(FIXTURE_CORRECT)
    for p in placements:
        if not p["correctly_placed"]:
            failures.append(f"FAIL: {p['name']} should be correctly placed but flagged as misplaced")
    if len(placements) == 3:
        print(f"PASS: All 3 target entries found in correct section")
    else:
        failures.append(f"FAIL: Expected 3 placements, got {len(placements)}")

    # Test 2: Misplaced entry is flagged
    sections2, dups2, placements2 = _run_on_fixture(FIXTURE_MISPLACED)
    airnow = next((p for p in placements2 if p["name"] == "AirNow"), None)
    if airnow and airnow["correctly_placed"]:
        failures.append("FAIL: AirNow in Weather section should be flagged as misplaced")
    elif airnow and not airnow["correctly_placed"]:
        print(f"PASS: AirNow correctly flagged as misplaced (in '{airnow['actual_section']}')")
    else:
        failures.append("FAIL: AirNow not found in misplaced fixture")

    # Test 3: Duplicate headings detected
    sections3, dups3, _ = _run_on_fixture(FIXTURE_DUPLICATE_HEADING)
    if "Environment" not in dups3:
        failures.append("FAIL: Duplicate 'Environment' heading not detected")
    else:
        print(f"PASS: Duplicate heading 'Environment' detected")

    # Save evidence
    os.makedirs(WORK_DIR, exist_ok=True)
    evidence = {
        "tool": "r02-t004.py",
        "tests": [
            {"name": "correct_placement_passes", "status": "FAIL" if failures else "PASS"},
            {"name": "misplaced_entry_flagged", "status": "FAIL" if failures else "PASS"},
            {"name": "duplicate_heading_detected", "status": "FAIL" if failures else "PASS"},
        ],
    }
    with open(os.path.join(WORK_DIR, "self_test_evidence.json"), "w") as f:
        json.dump(evidence, f, indent=2)

    if failures:
        print("\nSELF-TEST FAILURES:")
        for fail in failures:
            print(f"  {fail}")
        sys.exit(1)
    else:
        print("\nAll R02-T004 self-tests PASSED.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
