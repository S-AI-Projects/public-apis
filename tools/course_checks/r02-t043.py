#!/usr/bin/env python3
"""
R02-T043: Check category placement: Personality [README.md]
Map the selected entries to the named category and flag misplaced or
repeated headings without reclassifying entries solely from keywords.
Selected entries:
  - Advice Slip: http://api.adviceslip.com/
  - Astro Agents: https://astro-agent.dev/llms.txt
  - AstroWay: https://api.astroway.info/docs/
"""

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"
CATEGORY = "Personality"

SELECTED = {
    "http://api.adviceslip.com/": ("Advice Slip", "Personality"),
    "https://astro-agent.dev/llms.txt": ("Astro Agents", "Personality"),
    "https://api.astroway.info/docs/": ("AstroWay", "Personality"),
}


def scan_entries(lines):
    """Scan categories and API entries from markdown lines."""
    categories = defaultdict(list)
    entries = {}
    current_category = None
    in_catalogue = False

    for number, line in enumerate(lines, 1):
        stripped = line.strip()

        if stripped == "## Index":
            in_catalogue = True
            continue
        if stripped.startswith("## ") and in_catalogue:
            break
        if not in_catalogue:
            continue

        if stripped.startswith("### "):
            current_category = stripped[4:].strip()
            categories[current_category].append(number)

        elif current_category and line.startswith("|"):
            for url, (name, _) in SELECTED.items():
                if url in line:
                    entries[url] = {
                        "name": name,
                        "category": current_category,
                        "line": number,
                        "url": url,
                    }

    return categories, entries


def check_categories(lines):
    """Validate category consistency and repeated headings."""
    categories, entries = scan_entries(lines)
    errors = []

    for url, (name, expected) in SELECTED.items():
        if url not in entries:
            errors.append(f"Missing: {name} ({url})")
            continue

        item = entries[url]
        actual = item["category"]
        line = item["line"]
        if actual != expected:
            errors.append(
                f"Misplaced: {name}, category={actual}, "
                f"expected={expected}, line={line}"
            )

    for name, numbers in categories.items():
        if len(numbers) > 1:
            errors.append(f"Repeated heading: {name}, lines={numbers}")

    return errors, entries


def run_self_tests():
    """Run offline fixture tests."""
    try:
        assert False
        print("ERROR: assertions disabled (python -O/-OO); refusing false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    fixtures_dir = ROOT / "work" / "R02-T043" / "fixtures"

    def load_fixture(name):
        path = fixtures_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Fixture missing: {path}")
        return path.read_text(encoding="utf-8").splitlines()

    # 1. Valid fixture
    errors, entries = check_categories(load_fixture("valid.md"))
    assert not errors, f"Valid fixture produced unexpected errors: {errors}"
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"

    # 2. Misplaced fixture
    errors, _ = check_categories(load_fixture("misplaced.md"))
    misplaced_errors = [e for e in errors if "Misplaced:" in e]
    assert len(misplaced_errors) == 3, f"Expected 3 misplaced errors, got {len(misplaced_errors)}"

    # 3. Repeated heading fixture
    errors, _ = check_categories(load_fixture("repeated-heading.md"))
    repeated_errors = [e for e in errors if "Repeated heading: Personality" in e]
    assert len(repeated_errors) >= 1, "Expected repeated heading error for Personality"

    # 4. Missing entry fixture
    errors, _ = check_categories(load_fixture("missing-entry.md"))
    missing_errors = [e for e in errors if "Missing: AstroWay" in e]
    assert len(missing_errors) >= 1, "Expected missing entry error for AstroWay"

    # Write actual results
    work_dir = ROOT / "work" / "R02-T043"
    work_dir.mkdir(parents=True, exist_ok=True)
    actual_results = {
        "self_test": "passed",
        "fixtures_passed": 4,
        "category_verified": CATEGORY,
    }
    with open(work_dir / "actual-results.json", "w", encoding="utf-8") as f:
        json.dump(actual_results, f, indent=2)

    print("Self-test passed: 4 fixture checks (valid, misplaced, repeated-heading, missing-entry).")


def main():
    parser = argparse.ArgumentParser(description="Check category consistency for Personality APIs")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture checks")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if not README.exists():
        print(f"ERROR: {README} does not exist", file=sys.stderr)
        sys.exit(1)

    lines = README.read_text(encoding="utf-8").splitlines()
    errors, entries = check_categories(lines)

    for _, data in entries.items():
        print(f"{data['name']}: {data['category']} (line {data['line']})")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        sys.exit(1)

    print("Category consistency check passed.")
    sys.exit(0)


if __name__ == "__main__":
    main()
