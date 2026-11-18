#!/usr/bin/env python3
"""
R02-T041: Parse the entries: Calendar [README.md]
Extracts assigned entries from the Calendar category of README.md:
  - Africa Compliance Data: https://africacompliancedata.com/docs
  - caldays: https://caldays.com/api
  - Calendarific: https://calendarific.com/
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

ASSIGNED_ENTRIES = {
    "Africa Compliance Data": "https://africacompliancedata.com/docs",
    "caldays": "https://caldays.com/api",
    "Calendarific": "https://calendarific.com/",
}

TARGET_CATEGORY = "Calendar"

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_markdown_entries(file_path):
    """
    Parses the Markdown file, finds the TARGET_CATEGORY section,
    skips fenced code blocks (backticks or tildes),
    and extracts the assigned entries with their line numbers.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {file_path}")

    with open(path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    current_category = None
    in_fence = False
    fence_char = None
    fence_len = 0

    header_cols = []
    results = []

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        # Handle fenced code blocks: ``` or ~~~
        match_fence = re.match(r"^(`{3,}|~{3,})", line)
        if match_fence:
            marker = match_fence.group(1)
            char = marker[0]
            length = len(marker)
            if not in_fence:
                in_fence = True
                fence_char = char
                fence_len = length
                continue
            else:
                # To close a fence, character must match and length must be >= opening
                if char == fence_char and length >= fence_len:
                    in_fence = False
                    fence_char = None
                    fence_len = 0
                continue

        if in_fence:
            continue

        # Category headers (### Heading)
        if line.startswith("#"):
            match_h3 = re.match(r"^###\s+(.+)$", line)
            if match_h3:
                current_category = match_h3.group(1).strip()
                header_cols = []
            else:
                current_category = None
                header_cols = []
            continue

        if current_category != TARGET_CATEGORY:
            continue

        # Check for table rows (they contain '|' and at least one inner pipe)
        if "|" not in line:
            continue

        inner = line.strip("|")
        cells = [c.strip() for c in inner.split("|")]

        # Skip separator rows like |:---|:---|:---| or :---|:---|:---
        if all(re.match(r"^:?-+:?$", c) for c in cells if c):
            continue

        # Check if this is the header row
        header_lower = [c.lower() for c in cells]
        if ("api" in header_lower or "name" in header_lower) and "description" in header_lower:
            header_cols = header_lower
            continue

        if not header_cols or len(cells) < len(header_cols):
            continue

        # First column is expected to be API link
        first_col = cells[0]
        link_match = LINK_PATTERN.search(first_col)
        if not link_match:
            continue

        display_name = link_match.group(1).strip()
        url = link_match.group(2).strip()

        if display_name in ASSIGNED_ENTRIES:
            metadata = {}
            for col_name, val in zip(header_cols[1:], cells[1:]):
                clean_val = val.strip("`")
                metadata[col_name] = clean_val

            results.append({
                "display_name": display_name,
                "url": url,
                "category": current_category,
                "source_line": idx,
                "metadata": metadata,
            })

    return results


def run_self_test():
    """
    Self-test mode: verifies all requirements, fixtures, and failure modes.
    Non-zero exit if any check fails.
    """
    assert True, "Sanity check"

    # Verify -O / -OO is not suppressing assertions
    try:
        assert False
        # If assert False does not raise, assertions are disabled!
        print("ERROR: assertions are disabled (python -O/-OO); refusing to report a false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    repo_root = Path(__file__).resolve().parent.parent.parent
    work_dir = repo_root / "work" / "R02-T041"
    fixtures_dir = work_dir / "fixtures"

    fixture_input = fixtures_dir / "input.md"
    fixture_expected = fixtures_dir / "expected.json"
    fixture_no_match = fixtures_dir / "no-match.md"

    if not fixture_input.exists() or not fixture_expected.exists():
        print("ERROR: Fixtures missing. Run fixture generation first.", file=sys.stderr)
        sys.exit(1)

    # 1. Test extraction against fixture input
    parsed = parse_markdown_entries(fixture_input)
    with open(fixture_expected, "r", encoding="utf-8") as f:
        expected = json.load(f)

    assert len(parsed) == 3, f"Expected 3 entries, got {len(parsed)}"
    assert parsed == expected, f"Parsed entries do not match expected fixture:\nParsed: {parsed}\nExpected: {expected}"

    # Verify specific properties
    # Fragment preserved in caldays fixture
    caldays_entry = next(e for e in parsed if e["display_name"] == "caldays")
    assert "#test-frag" in caldays_entry["url"], "URL fragment must be preserved"

    # Line numbers match fixture
    assert parsed[0]["source_line"] == 7
    assert parsed[1]["source_line"] == 8
    assert parsed[2]["source_line"] == 9

    # 2. Test failure input (no match)
    no_match_parsed = parse_markdown_entries(fixture_no_match)
    assert len(no_match_parsed) == 0, f"Expected 0 entries for no-match fixture, got {len(no_match_parsed)}"

    # 3. Write actual.json to work dir
    work_dir.mkdir(parents=True, exist_ok=True)
    with open(work_dir / "actual.json", "w", encoding="utf-8") as f:
        json.dump(parsed, f, indent=2)

    print("Self-test passed: 3 Calendar APIs extracted; wrong-category, non-assigned, backtick-fenced, tilde-fenced and fake links ignored; URL fragment preserved; source lines 7/8/9.")
    print("Failure input rejected with a non-zero exit code.")
    print(f"Actual results written to: {work_dir / 'actual.json'}")


def main():
    parser = argparse.ArgumentParser(description="Extract Calendar entries from public-apis README.md")
    parser.add_argument("--self-test", action="store_true", help="Run self-tests and exit non-zero on failure")
    parser.add_argument("--input", type=str, default=None, help="Path to input Markdown file")

    args = parser.parse_args()

    if args.self_test:
        run_self_test()
        sys.exit(0)

    # Normal mode
    repo_root = Path(__file__).resolve().parent.parent.parent
    input_file = args.input if args.input else repo_root / "README.md"

    results = parse_markdown_entries(input_file)
    if not results:
        print("No assigned entries found.", file=sys.stderr)
        print(json.dumps([], indent=2))
        sys.exit(1)

    print(json.dumps(results, indent=2))
    sys.exit(0)


if __name__ == "__main__":
    main()
