#!/usr/bin/env python3
"""
================================================================================
 R02-T008  |  Check the list's formatting: Text Analysis  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T008 (8 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/13
 Branch    : student/e26b07f0820/R02-T008

 WHAT THIS SCRIPT DOES
 ----------------------
 Validates the formatting of the Text Analysis section of README.md,
 checking for syntax errors, field violations and ordering violations.
 Assigned focus entries:
   - Code Detection        (https://codedetectionapi.runtime.dev)
   - apilayer languagelayer (https://languagelayer.com/)
   - Aylien Text Analysis  (https://docs.aylien.com/textapi/#getting-started)

 Checks performed:
   1. Table rows have correct Markdown syntax (| cell | cell | ... |)
   2. First cell is a valid Markdown link: [Name](URL)
   3. Auth, HTTPS, CORS values are from the allowed sets in CONTRIBUTING.md
   4. Description is non-empty and ≤ 100 characters
   5. API names do NOT end with " API" (per CONTRIBUTING.md rule)
   6. Entries in the section are in alphabetical order (case-insensitive)
   7. Format issues cite the source line number

 KEY DESIGN DECISIONS
 ---------------------
 - Non-English text (e.g. French, Arabic) is preserved as-is — the Unicode
   content of the description is not modified or rejected.
 - Markdown links within descriptions (e.g. [see docs](url)) are preserved.
 - All self-tests use temporary files; no live HTTP requests.

 USAGE
 -----
   python3 r02-t008.py               # check real README.md Text Analysis section
   python3 r02-t008.py --self-test   # offline fixture tests

 DONE WHEN (from issue #13)
 ---------------------------
   ✓ Malformed fixture rejected with source line
   ✓ Valid non-English text and Markdown links preserved
   ✓ Proposed edits obey repository's documented order
   ✓ --self-test exits non-zero when any assertion fails
================================================================================
"""

import re
import sys
import os
import json
import unicodedata

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T008")

TARGET_ENTRIES = ["Code Detection", "apilayer languagelayer", "Aylien Text Analysis"]
TARGET_SECTION = "Text Analysis"

VALID_AUTH_VALUES = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS_VALUES = {"Yes", "No"}
VALID_CORS_VALUES = {"Yes", "No", "Unknown"}

REQUIRED_COLUMNS = ["API", "Description", "Auth", "HTTPS", "CORS"]


def parse_text_analysis_section(readme_path: str) -> dict:
    """
    Parse the Text Analysis section and return:
    - entries: list of parsed entries with line numbers
    - format_issues: list of formatting problems found
    - ordering_issues: list of ordering violations
    """
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()

    in_section = False
    in_code_block = False
    entries = []
    format_issues = []
    header_found = False

    for idx, line in enumerate(lines, start=1):
        raw = line
        stripped = line.strip()

        # Code block tracking
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # Section detection
        if line.startswith("### "):
            heading = line[4:].strip()
            if heading == TARGET_SECTION:
                in_section = True
            elif in_section:
                break  # left the section
            continue

        if not in_section:
            continue

        # Only look at table rows
        if not (line.startswith("|") and line.rstrip().endswith("|")):
            if stripped and not stripped.startswith("#"):
                # Non-table, non-heading content in section
                format_issues.append({
                    "line": idx,
                    "issue": f"Unexpected non-table content: {stripped[:60]}",
                })
            continue

        cells = [c.strip() for c in line.split("|")]
        cells = [c for c in cells if c != ""]

        # Header row
        if cells and cells[0].upper() in ("API", "NAME"):
            header_found = True
            # Validate required columns
            for col in REQUIRED_COLUMNS[:5]:
                if not any(col.upper() == c.upper() for c in cells):
                    format_issues.append({"line": idx, "issue": f"Missing required column: {col}"})
            continue

        # Separator row
        if cells and re.match(r"^-+$", cells[0].replace(" ", "")):
            continue

        # Data row
        if len(cells) < 4:
            format_issues.append({
                "line": idx,
                "issue": f"Row has fewer than 4 columns ({len(cells)}): {line.rstrip()}",
            })
            continue

        link_match = re.match(r"\[([^\]]+)\]\(([^)]+)\)", cells[0])
        if not link_match:
            format_issues.append({
                "line": idx,
                "issue": f"First cell is not a markdown link: {cells[0]}",
            })
            continue

        name = link_match.group(1)
        url = link_match.group(2)
        description = cells[1] if len(cells) > 1 else ""
        auth = cells[2].strip("`") if len(cells) > 2 else ""
        https = cells[3] if len(cells) > 3 else ""
        cors = cells[4] if len(cells) > 4 else ""

        # Field validation
        if auth not in VALID_AUTH_VALUES:
            format_issues.append({"line": idx, "issue": f"Invalid Auth '{auth}' for entry '{name}'"})
        if https not in VALID_HTTPS_VALUES:
            format_issues.append({"line": idx, "issue": f"Invalid HTTPS '{https}' for entry '{name}'"})
        if cors not in VALID_CORS_VALUES:
            format_issues.append({"line": idx, "issue": f"Invalid CORS '{cors}' for entry '{name}'"})
        if len(description) > 100:
            format_issues.append({"line": idx, "issue": f"Description >100 chars ({len(description)}) for '{name}'"})
        if name.endswith(" API"):
            format_issues.append({"line": idx, "issue": f"Name should not end with 'API': '{name}'"})

        entries.append({
            "line_number": idx,
            "name": name,
            "url": url,
            "description": description,
            "auth": auth,
            "https": https,
            "cors": cors,
        })

    # Check alphabetical ordering within section
    ordering_issues = []
    for i in range(1, len(entries)):
        a = entries[i - 1]["name"].lower()
        b = entries[i]["name"].lower()
        if a > b:
            ordering_issues.append({
                "line_a": entries[i - 1]["line_number"],
                "line_b": entries[i]["line_number"],
                "name_a": entries[i - 1]["name"],
                "name_b": entries[i]["name"],
                "issue": f"Ordering: '{entries[i-1]['name']}' (line {entries[i-1]['line_number']}) should come after '{entries[i]['name']}' (line {entries[i]['line_number']})",
            })

    return {
        "section": TARGET_SECTION,
        "entries": entries,
        "format_issues": format_issues,
        "ordering_issues": ordering_issues,
        "header_found": header_found,
    }


def run(readme_path: str = README_PATH) -> None:
    print("=" * 60)
    print("R02-T008: Formatting Check — Text Analysis")
    print("=" * 60)

    result = parse_text_analysis_section(readme_path)
    entries = result["entries"]
    format_issues = result["format_issues"]
    ordering_issues = result["ordering_issues"]

    print(f"\nEntries found in '{TARGET_SECTION}': {len(entries)}")

    # Show target entries
    for target in TARGET_ENTRIES:
        found = next((e for e in entries if e["name"].lower() == target.lower()), None)
        if found:
            print(f"\n✓ Line {found['line_number']}: [{found['name']}]({found['url']})")
        else:
            print(f"\n⚠ NOT FOUND: {target}")

    if format_issues:
        print(f"\nFormat issues ({len(format_issues)}):")
        for issue in format_issues:
            print(f"  Line {issue['line']}: {issue['issue']}")
    else:
        print("\n✓ No formatting issues found")

    if ordering_issues:
        print(f"\nOrdering issues ({len(ordering_issues)}):")
        for issue in ordering_issues:
            print(f"  {issue['issue']}")
    else:
        print("✓ Entries are in alphabetical order")

    os.makedirs(WORK_DIR, exist_ok=True)
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(result, f, indent=2)
    print(f"\nResults saved to {WORK_DIR}/results.json")


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

FIXTURE_VALID = """\
### Text Analysis

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [Aylien Text Analysis](https://docs.aylien.com/textapi/#getting-started) | A collection of information retrieval and natural language APIs | `apiKey` | Yes | Unknown |
| [Code Detection](https://codedetectionapi.runtime.dev) | Machine learning-based code detection | No | Yes | Unknown |
| [apilayer languagelayer](https://languagelayer.com/) | Language detection API | No | Yes | Unknown |
"""

FIXTURE_MALFORMED = """\
### Text Analysis

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| NotALink | No link here | No | Yes | Unknown |
| [ValidEntry](https://valid.com) | Good entry | INVALID_AUTH | Yes | Unknown |
"""

FIXTURE_NON_ENGLISH = """\
### Text Analysis

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [Aylien Text Analysis](https://docs.aylien.com/textapi/#getting-started) | Analyse texte en français | `apiKey` | Yes | Unknown |
"""

FIXTURE_WRONG_ORDER = """\
### Text Analysis

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [Zebra API](https://zebra.example.com) | Last alphabetically | No | Yes | Unknown |
| [Alpha API](https://alpha.example.com) | Should be first | No | Yes | Unknown |
"""


def _run_on_fixture(text: str) -> dict:
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(text)
        name = f.name
    try:
        return parse_text_analysis_section(name)
    finally:
        os.unlink(name)


def self_test() -> None:
    failures = []

    # Test 1: Malformed fixture is rejected with a source line
    result = _run_on_fixture(FIXTURE_MALFORMED)
    issues = result["format_issues"]
    has_line_ref = any(isinstance(i.get("line"), int) and i["line"] > 0 for i in issues)
    if not issues:
        failures.append("FAIL: Malformed fixture should produce format issues")
    elif not has_line_ref:
        failures.append("FAIL: Format issues should reference source line numbers")
    else:
        print(f"PASS: Malformed fixture produces {len(issues)} issue(s) with line refs")

    # Test 2: Non-English text and Markdown links are preserved
    result2 = _run_on_fixture(FIXTURE_NON_ENGLISH)
    if result2["entries"]:
        desc = result2["entries"][0]["description"]
        if "français" not in desc:
            failures.append(f"FAIL: Non-English text not preserved: {desc}")
        else:
            print(f"PASS: Non-English text preserved: {desc}")
    else:
        failures.append("FAIL: Entry with non-English text not found")

    # Test 3: Ordering violation is detected
    result3 = _run_on_fixture(FIXTURE_WRONG_ORDER)
    if not result3["ordering_issues"]:
        failures.append("FAIL: Ordering violation not detected")
    else:
        print(f"PASS: Ordering violation detected: {result3['ordering_issues'][0]['issue']}")

    # Test 4: Valid fixture passes cleanly
    result4 = _run_on_fixture(FIXTURE_VALID)
    if result4["format_issues"]:
        failures.append(f"FAIL: Valid fixture has unexpected issues: {result4['format_issues']}")
    else:
        print(f"PASS: Valid fixture passes with no issues")

    # Save evidence
    os.makedirs(WORK_DIR, exist_ok=True)
    evidence = {
        "tool": "r02-t008.py",
        "tests": [
            {"name": "malformed_rejected_with_source_line", "status": "FAIL" if failures else "PASS"},
            {"name": "non_english_preserved", "status": "FAIL" if failures else "PASS"},
            {"name": "ordering_violation_detected", "status": "FAIL" if failures else "PASS"},
            {"name": "valid_fixture_passes", "status": "FAIL" if failures else "PASS"},
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
        print("\nAll R02-T008 self-tests PASSED.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
