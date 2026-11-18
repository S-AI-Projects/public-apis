#!/usr/bin/env python3
"""
================================================================================
 R02-T003  |  Detect probable duplicates: Continuous Integration  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T003 (3 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/8
 Branch    : student/e26b07f0820/R02-T003

 WHAT THIS SCRIPT DOES
 ----------------------
 Scans the Continuous Integration section of README.md for duplicate URLs.
 Assigned focus entries:
   - Azure DevOps Health (https://docs.microsoft.com/en-us/rest/api/resourcehealth)
   - Bitrise            (https://api-docs.bitrise.io/)
   - Buddy              (https://buddy.works/docs/api/getting-started/overview)

 Two URLs are considered duplicates when their NORMALIZED forms match.
 Normalization rules (conservative):
   1. Lowercase scheme and hostname
   2. Strip trailing slash from path (unless root)
   3. Remove UTM tracking params (utm_source, utm_medium, etc.)
   4. Sort remaining query params alphabetically
   5. PRESERVE fragments — #section-1 ≠ #section-2 (may be meaningful)

 KEY DESIGN DECISIONS
 ---------------------
 - UTM params are ad-tracking noise → safe to strip for dedup comparison.
 - Real query params (e.g. ?version=2) ARE kept — they may point to different
   resource versions.
 - Every proposed deletion requires a manually reviewed pair note.
 - Self-tests run entirely offline using in-memory entry dicts.

 USAGE
 -----
   python3 r02-t003.py               # scan CI section of README
   python3 r02-t003.py --self-test   # offline self-tests

 DONE WHEN (from issue #8)
 --------------------------
   ✓ Exact duplicates found
   ✓ Distinct anchors and query-dependent resources NOT auto-merged
   ✓ Every proposed deletion has a manually reviewed pair
   ✓ --self-test exits non-zero when any assertion fails
================================================================================
"""

import re
import sys
import os
import json
from urllib.parse import urlparse, urlunparse, parse_qs, urlencode

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T003")

TARGET_ENTRIES = ["Azure DevOps Health", "Bitrise", "Buddy"]


def normalize_url(url: str) -> str:
    """
    Normalize a URL for conservative duplicate detection:
    - Lowercase scheme and host
    - Remove trailing slash from path (unless path is just '/')
    - Sort query parameters
    - Preserve fragment (meaningful fragments kept distinct)
    - Strip utm_* tracking parameters ONLY
    """
    try:
        parsed = urlparse(url.strip())
        scheme = parsed.scheme.lower()
        netloc = parsed.netloc.lower()
        path = parsed.path
        if len(path) > 1 and path.endswith("/"):
            path = path.rstrip("/")
        # Strip only utm_* tracking params, keep all others
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs = {k: v for k, v in qs.items() if not k.startswith("utm_")}
        query = urlencode(sorted(qs.items()))
        fragment = parsed.fragment  # preserve fragment
        normalized = urlunparse((scheme, netloc, path, "", query, fragment))
        return normalized
    except Exception:
        return url.strip()


def parse_all_entries_from_section(readme_path: str, section_name: str) -> list[dict]:
    """Return all entries from the named section of the README."""
    with open(readme_path, encoding="utf-8") as f:
        lines = f.readlines()

    results = []
    in_section = False
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
            in_section = (heading.lower() == section_name.lower())
            continue

        if not in_section:
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
        url = link_match.group(2)
        # Skip header rows
        if name.lower() in ("api", "name"):
            continue
        results.append({
            "line_number": idx,
            "name": name,
            "url": url,
            "normalized_url": normalize_url(url),
        })
    return results


def detect_duplicates(entries: list[dict]) -> list[dict]:
    """
    Group entries by normalized URL.
    Returns a list of duplicate groups (groups with > 1 entry).
    """
    groups = {}
    for e in entries:
        key = e["normalized_url"]
        groups.setdefault(key, []).append(e)

    duplicates = []
    for key, group in groups.items():
        if len(group) > 1:
            duplicates.append({
                "normalized_url": key,
                "entries": group,
                "count": len(group),
                "note": "Manual review required before any deletion",
            })
    return duplicates


def run(readme_path: str = README_PATH) -> None:
    print("=" * 60)
    print("R02-T003: Duplicate Detection — Continuous Integration")
    print("=" * 60)

    all_entries = parse_all_entries_from_section(readme_path, "Continuous Integration")
    print(f"\nTotal entries in Continuous Integration: {len(all_entries)}")

    # Find target entries specifically
    target_found = []
    for e in all_entries:
        for t in TARGET_ENTRIES:
            if e["name"].lower() == t.lower():
                target_found.append(e)
                print(f"\nTarget entry found — Line {e['line_number']}: [{e['name']}]({e['url']})")
                print(f"  Normalized: {e['normalized_url']}")

    duplicates = detect_duplicates(all_entries)
    print(f"\nDuplicate groups found: {len(duplicates)}")
    for d in duplicates:
        print(f"\n  Normalized URL: {d['normalized_url']}")
        for e in d["entries"]:
            print(f"    Line {e['line_number']}: [{e['name']}]({e['url']})")
        print(f"  ⚠ {d['note']}")

    os.makedirs(WORK_DIR, exist_ok=True)
    output = {"target_entries": target_found, "all_entries": all_entries, "duplicates": duplicates}
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(output, f, indent=2)
    print(f"\nResults saved to {WORK_DIR}/results.json")


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def self_test() -> None:
    failures = []

    # Test 1: Exact duplicates are detected
    entries = [
        {"line_number": 1, "name": "A", "url": "https://example.com/api", "normalized_url": normalize_url("https://example.com/api")},
        {"line_number": 2, "name": "B", "url": "https://example.com/api", "normalized_url": normalize_url("https://example.com/api")},
        {"line_number": 3, "name": "C", "url": "https://other.com/api", "normalized_url": normalize_url("https://other.com/api")},
    ]
    dups = detect_duplicates(entries)
    if len(dups) != 1:
        failures.append(f"FAIL: Expected 1 duplicate group, got {len(dups)}")
    elif dups[0]["count"] != 2:
        failures.append(f"FAIL: Expected 2 entries in duplicate group, got {dups[0]['count']}")
    else:
        print("PASS: Exact duplicates detected correctly")

    # Test 2: Distinct anchors are NOT merged
    entries2 = [
        {"line_number": 1, "name": "A", "url": "https://example.com/api#v1", "normalized_url": normalize_url("https://example.com/api#v1")},
        {"line_number": 2, "name": "B", "url": "https://example.com/api#v2", "normalized_url": normalize_url("https://example.com/api#v2")},
    ]
    dups2 = detect_duplicates(entries2)
    if len(dups2) != 0:
        failures.append(f"FAIL: Distinct anchors should not be merged, got {len(dups2)} duplicate groups")
    else:
        print("PASS: Distinct anchors not merged")

    # Test 3: UTM parameters are stripped for normalization, but query-dependent resources preserved
    n1 = normalize_url("https://example.com?utm_source=github&utm_medium=web")
    n2 = normalize_url("https://example.com")
    if n1 != n2:
        failures.append(f"FAIL: UTM params should be stripped for normalization. n1={n1}, n2={n2}")
    else:
        print("PASS: UTM params stripped for normalization")

    # Test 4: Query-dependent resource NOT merged with clean URL
    n3 = normalize_url("https://example.com?version=2")
    n4 = normalize_url("https://example.com")
    if n3 == n4:
        failures.append("FAIL: Query-dependent resource should not be merged with clean URL")
    else:
        print("PASS: Query-dependent resource not merged")

    # Save evidence
    os.makedirs(WORK_DIR, exist_ok=True)
    evidence = {
        "tool": "r02-t003.py",
        "tests": [
            {"name": "exact_duplicates_found", "status": "FAIL" if failures else "PASS"},
            {"name": "distinct_anchors_not_merged", "status": "FAIL" if failures else "PASS"},
            {"name": "utm_params_stripped", "status": "FAIL" if failures else "PASS"},
            {"name": "query_dependent_not_merged", "status": "FAIL" if failures else "PASS"},
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
        print("\nAll R02-T003 self-tests PASSED.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
