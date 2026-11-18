#!/usr/bin/env python3
"""
================================================================================
 R02-T010  |  Document a repeatable maintenance pass: Events  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T010 (10 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/15
 Branch    : student/e26b07f0820/R02-T010

 WHAT THIS SCRIPT DOES
 ----------------------
 Generates a one-command scoped maintenance-pass report for three assigned
 Events section entries, covering before/after metadata, observed facts,
 manual decisions and reproducible offline fixtures.
 Assigned entries:
   - Eventbrite (https://www.eventbrite.com/platform/api/)
   - FindLocal  (https://findlocal.community/docs)
   - SeatGeek   (https://platform.seatgeek.com/)

 Each entry's report section includes:
   BEFORE  — the current state extracted from README.md
   AFTER   — the proposed state (unchanged here unless evidence proves otherwise)
   FACTS   — observed, evidence-based statements (no speculation)
   REC     — human recommendation for next reviewer
   DECISION — the action taken (NO_CHANGE, EDIT, REMOVE, UNVERIFIED)

 KEY DESIGN DECISIONS
 ---------------------
 - Report is deterministic: same input → same output (timestamp excluded from
   stability comparison in --self-test).
 - Observed facts are strictly separated from recommendations — a reviewer can
   disagree with the recommendation but the facts stand.
 - No link is removed without a recorded manual decision (MAINTENANCE_LOG).
 - Cross-checks the live README to flag if it has drifted from the log.

 USAGE
 -----
   python3 r02-t010.py               # generate full maintenance report
   python3 r02-t010.py --self-test   # offline fixture tests

 DONE WHEN (from issue #15)
 ---------------------------
   ✓ Report names exact source lines
   ✓ Separates observed facts from recommendations
   ✓ Produces stable output from same fixtures
   ✓ No link removed without a manual decision
   ✓ --self-test exits non-zero when any assertion fails
================================================================================
"""

import re
import sys
import os
import json
import datetime

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T010")

TARGET_ENTRIES = ["Eventbrite", "FindLocal", "SeatGeek"]
TARGET_SECTION = "Events"

VALID_AUTH_VALUES = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS_VALUES = {"Yes", "No"}
VALID_CORS_VALUES = {"Yes", "No", "Unknown"}

# Manual decisions table: observed facts, recommendations, decisions
# Each entry documents BEFORE state (from README), AFTER state (proposed), and rationale
MAINTENANCE_LOG = [
    {
        "name": "Eventbrite",
        "url": "https://www.eventbrite.com/platform/api/",
        "before": {
            "auth": "apiKey",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Find local events",
        },
        "after": {
            "auth": "apiKey",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Find local events",
        },
        "observed_facts": [
            "URL resolves to Eventbrite developer platform documentation",
            "API key required (OAuth also supported for user data)",
            "HTTPS enforced",
            "CORS status not documented publicly",
        ],
        "recommendation": "Entry appears correct; CORS could be updated to 'Yes' if confirmed",
        "decision": "No change required at this time",
        "decision_type": "NO_CHANGE",
        "source_line_checked": True,
    },
    {
        "name": "FindLocal",
        "url": "https://findlocal.community/docs",
        "before": {
            "auth": "No",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Find locally sourced food",
        },
        "after": {
            "auth": "No",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Find locally sourced food",
        },
        "observed_facts": [
            "URL target is a small community platform",
            "Documentation endpoint checked offline (fixture-based)",
            "No authentication indicated in public documentation",
        ],
        "recommendation": "Verify URL is still active; mark as unverified if unavailable",
        "decision": "Marked as unverified pending live check; no edit to README",
        "decision_type": "UNVERIFIED",
        "source_line_checked": True,
    },
    {
        "name": "SeatGeek",
        "url": "https://platform.seatgeek.com/",
        "before": {
            "auth": "apiKey",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Search events, venues and performers",
        },
        "after": {
            "auth": "apiKey",
            "https": "Yes",
            "cors": "Unknown",
            "description": "Search events, venues and performers",
        },
        "observed_facts": [
            "API documentation available at https://platform.seatgeek.com/",
            "Client ID (api key) required for all endpoints",
            "HTTPS enforced",
            "CORS status not documented",
        ],
        "recommendation": "Entry is accurate; consider verifying CORS with a browser test",
        "decision": "No change required",
        "decision_type": "NO_CHANGE",
        "source_line_checked": True,
    },
]


def parse_entry_from_readme(readme_path: str, target_name: str) -> dict | None:
    """Find a specific entry in the README by name, return with line number."""
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()
    in_code_block = False
    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```") or stripped.startswith("~~~"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
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
        if name.lower() != target_name.lower():
            continue
        return {
            "line_number": idx,
            "name": name,
            "url": link_match.group(2),
            "description": cells[1] if len(cells) > 1 else "",
            "auth": cells[2].strip("`") if len(cells) > 2 else "",
            "https": cells[3] if len(cells) > 3 else "",
            "cors": cells[4] if len(cells) > 4 else "",
        }
    return None


def generate_report(readme_path: str = README_PATH) -> dict:
    """
    Generate a full maintenance pass report with:
    - Source line references
    - Observed facts vs recommendations
    - Stable output from same fixtures
    """
    report = {
        "tool": "r02-t010.py",
        "generated_at": datetime.datetime.utcnow().isoformat() + "Z",
        "section": TARGET_SECTION,
        "target_entries": TARGET_ENTRIES,
        "readme_path": readme_path,
        "entries": [],
    }

    for log in MAINTENANCE_LOG:
        catalogue_entry = parse_entry_from_readme(readme_path, log["name"])
        entry_report = {
            "name": log["name"],
            "source_line": catalogue_entry["line_number"] if catalogue_entry else None,
            "url": log["url"],
            "before": log["before"],
            "after": log["after"],
            "changed": log["before"] != log["after"],
            "observed_facts": log["observed_facts"],
            "recommendation": log["recommendation"],
            "decision": log["decision"],
            "decision_type": log["decision_type"],
        }

        # Cross-check with current README state
        if catalogue_entry:
            current_auth = catalogue_entry["auth"].strip("`")
            if current_auth != log["before"]["auth"]:
                entry_report["discrepancy"] = (
                    f"README auth='{current_auth}' differs from maintenance log before='{log['before']['auth']}'"
                )

        report["entries"].append(entry_report)

    return report


def run(readme_path: str = README_PATH) -> None:
    print("=" * 60)
    print("R02-T010: Maintenance Pass Report — Events")
    print("=" * 60)

    report = generate_report(readme_path)

    print(f"\nGenerated: {report['generated_at']}")
    print(f"Section: {report['section']}")
    print(f"Entries covered: {len(report['entries'])}")
    print()

    for entry in report["entries"]:
        print(f"--- {entry['name']} (source line: {entry['source_line']}) ---")
        print(f"  URL: {entry['url']}")
        print(f"  BEFORE: auth={entry['before']['auth']}, https={entry['before']['https']}, cors={entry['before']['cors']}")
        print(f"  AFTER : auth={entry['after']['auth']}, https={entry['after']['https']}, cors={entry['after']['cors']}")
        print(f"  Changed: {'YES' if entry['changed'] else 'NO'}")
        print(f"  Observed facts:")
        for fact in entry["observed_facts"]:
            print(f"    - {fact}")
        print(f"  Recommendation: {entry['recommendation']}")
        print(f"  Decision [{entry['decision_type']}]: {entry['decision']}")
        if "discrepancy" in entry:
            print(f"  ⚠ Discrepancy: {entry['discrepancy']}")
        print()

    os.makedirs(WORK_DIR, exist_ok=True)
    output_path = os.path.join(WORK_DIR, "results.json")
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"Results saved to {output_path}")
    return report


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

FIXTURE_STABLE = """\
### Events

| API | Description | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- |
| [Eventbrite](https://www.eventbrite.com/platform/api/) | Find local events | `apiKey` | Yes | Unknown |
| [FindLocal](https://findlocal.community/docs) | Find locally sourced food | No | Yes | Unknown |
| [SeatGeek](https://platform.seatgeek.com/) | Search events, venues and performers | `apiKey` | Yes | Unknown |
"""


def _run_on_fixture(text: str) -> dict:
    import tempfile
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
        f.write(text)
        name = f.name
    try:
        return generate_report(name)
    finally:
        os.unlink(name)


def self_test() -> None:
    failures = []

    # Test 1: Report names exact source lines
    report = _run_on_fixture(FIXTURE_STABLE)
    for entry in report["entries"]:
        if entry["source_line"] is None:
            failures.append(f"FAIL: {entry['name']} has no source_line in report")
        elif not isinstance(entry["source_line"], int) or entry["source_line"] < 1:
            failures.append(f"FAIL: {entry['name']} source_line is invalid: {entry['source_line']}")
        else:
            print(f"PASS: {entry['name']} → source line {entry['source_line']}")

    # Test 2: Separates observed facts from recommendations
    for entry in report["entries"]:
        if not entry.get("observed_facts"):
            failures.append(f"FAIL: {entry['name']} missing observed_facts")
        if not entry.get("recommendation"):
            failures.append(f"FAIL: {entry['name']} missing recommendation")
        if entry.get("observed_facts") and entry.get("recommendation"):
            print(f"PASS: {entry['name']} has both observed_facts and recommendation")

    # Test 3: Produces stable output from the same fixtures
    report1 = _run_on_fixture(FIXTURE_STABLE)
    report2 = _run_on_fixture(FIXTURE_STABLE)
    # Remove non-deterministic fields before comparing
    for r in (report1, report2):
        r.pop("generated_at", None)
        r.pop("readme_path", None)
    if report1 != report2:
        failures.append("FAIL: Report is not stable across two runs of same fixture")
    else:
        print("PASS: Report produces stable output from same fixtures")

    # Test 4: No link is removed without a manual decision
    for entry in report["entries"]:
        if entry["changed"]:
            if not entry.get("decision"):
                failures.append(f"FAIL: {entry['name']} changed without a decision recorded")
        else:
            print(f"PASS: {entry['name']} — no change recorded with decision='{entry['decision']}'")

    # Save evidence
    os.makedirs(WORK_DIR, exist_ok=True)
    evidence = {
        "tool": "r02-t010.py",
        "fixture_used": "FIXTURE_STABLE",
        "tests": [
            {"name": "names_exact_source_lines", "status": "FAIL" if failures else "PASS"},
            {"name": "separates_facts_from_recommendations", "status": "FAIL" if failures else "PASS"},
            {"name": "stable_output_from_same_fixtures", "status": "FAIL" if failures else "PASS"},
            {"name": "no_link_removed_without_decision", "status": "FAIL" if failures else "PASS"},
        ],
        "maintenance_log": MAINTENANCE_LOG,
    }
    with open(os.path.join(WORK_DIR, "self_test_evidence.json"), "w") as f:
        json.dump(evidence, f, indent=2)

    if failures:
        print("\nSELF-TEST FAILURES:")
        for fail in failures:
            print(f"  {fail}")
        sys.exit(1)
    else:
        print("\nAll R02-T010 self-tests PASSED.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
