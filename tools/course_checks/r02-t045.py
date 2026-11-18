#!/usr/bin/env python3
"""
R02-T045: Make checks work offline: Music [README.md]
Build a fixture-based offline test suite for parsing and validating the Music category in README.md.
Selected entries:
  - 7digital: https://docs.7digital.com/reference
  - AI Mastering: https://aimastering.com/api_docs/
  - Audiomack: https://www.audiomack.com/data-api/docs
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"
CATEGORY = "Music"

EXPECTED_ENTRIES = {
    "7digital": {
        "url": "https://docs.7digital.com/reference",
        "auth": "`OAuth`",
        "https": "Yes",
        "cors": "Unknown",
    },
    "AI Mastering": {
        "url": "https://aimastering.com/api_docs/",
        "auth": "`apiKey`",
        "https": "Yes",
        "cors": "Yes",
    },
    "Audiomack": {
        "url": "https://www.audiomack.com/data-api/docs",
        "auth": "`OAuth`",
        "https": "Yes",
        "cors": "Unknown",
    },
}

LINK_PATTERN = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")


def parse_music_table(lines):
    """
    Parses the Music category table in Markdown lines.
    Handles valid rows, malformed rows, and unusual URL characters.
    """
    in_section = False
    header_found = False
    entries = {}
    malformed_rows = []
    unusual_urls = []

    for idx, raw_line in enumerate(lines, start=1):
        line = raw_line.strip()

        if line.startswith("### "):
            cat = line[4:].strip()
            if cat == CATEGORY:
                in_section = True
                header_found = False
                continue
            elif in_section:
                break

        if not in_section:
            continue

        if not header_found:
            if "API" in line and "Description" in line and "Auth" in line and "HTTPS" in line and "CORS" in line:
                header_found = True
            continue

        # Skip separator
        if re.match(r"^\|?\s*:?-+:?\s*(\|:?-+:?\s*)+\|?$", line):
            continue

        if not line.startswith("|") or not line.endswith("|"):
            continue

        cells = [c.strip() for c in line[1:-1].split("|")]
        if len(cells) < 5:
            malformed_rows.append({"line": idx, "content": line, "reason": "Fewer than 5 columns"})
            continue

        api_cell, desc, auth, https, cors = cells[0], cells[1], cells[2], cells[3], cells[4]
        link_match = LINK_PATTERN.search(api_cell)
        if not link_match:
            malformed_rows.append({"line": idx, "content": line, "reason": "No valid markdown link in API column"})
            continue

        name = link_match.group(1).strip()
        url = link_match.group(2).strip()

        # Check for unusual URL characters (query, fragment, parentheses, percent-encoding)
        if any(c in url for c in ("?", "#", "(", ")", "%", "~", "&")):
            unusual_urls.append({"name": name, "url": url, "line": idx})

        entries[name] = {
            "name": name,
            "url": url,
            "description": desc,
            "auth": auth,
            "https": https,
            "cors": cors,
            "line": idx,
        }

    return entries, malformed_rows, unusual_urls


def run_self_tests():
    """Offline test suite exercising fixtures with explicit expected outcomes."""
    try:
        assert False
        print("ERROR: assertions disabled (python -O/-OO); refusing false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    fixtures_dir = ROOT / "work" / "R02-T045" / "fixtures"

    def read_fixture(name):
        path = fixtures_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Fixture not found: {path}")
        return path.read_text(encoding="utf-8").splitlines()

    # 1. Valid rows fixture
    entries, malformed, unusual = parse_music_table(read_fixture("valid.md"))
    assert len(entries) == 3, f"Expected 3 valid entries, got {len(entries)}"
    assert len(malformed) == 0, f"Expected 0 malformed rows, got {len(malformed)}"
    for name, exp in EXPECTED_ENTRIES.items():
        assert name in entries, f"Missing {name}"
        assert entries[name]["auth"] == exp["auth"]
        assert entries[name]["https"] == exp["https"]
        assert entries[name]["cors"] == exp["cors"]

    # 2. Malformed rows fixture (row with missing cell, row without markdown link)
    entries, malformed, unusual = parse_music_table(read_fixture("malformed.md"))
    assert len(malformed) == 2, f"Expected 2 malformed rows, got {len(malformed)}"

    # 3. Unusual URL characters fixture (query params, percent-encoding, anchors)
    entries, malformed, unusual = parse_music_table(read_fixture("unusual-urls.md"))
    assert len(unusual) >= 3, f"Expected at least 3 unusual URLs detected, got {len(unusual)}"

    # Save actual results
    work_dir = ROOT / "work" / "R02-T045"
    work_dir.mkdir(parents=True, exist_ok=True)
    actual_results = {
        "self_test": "passed",
        "fixtures_passed": ["valid.md", "malformed.md", "unusual-urls.md"],
        "network_access": "offline",
    }
    with open(work_dir / "actual-results.json", "w", encoding="utf-8") as f:
        json.dump(actual_results, f, indent=2)

    print("Self-test passed: offline fixture suite validated (valid rows, malformed rows, unusual URLs).")


def main():
    parser = argparse.ArgumentParser(description="Offline parser and validator for Music APIs")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture checks")
    parser.add_argument("--readme", type=str, default=None, help="Path to markdown file")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    target_file = Path(args.readme) if args.readme else README
    if not target_file.exists():
        print(f"ERROR: {target_file} not found", file=sys.stderr)
        sys.exit(1)

    lines = target_file.read_text(encoding="utf-8").splitlines()
    entries, malformed, unusual = parse_music_table(lines)

    for name in EXPECTED_ENTRIES:
        if name in entries:
            e = entries[name]
            print(f"OK line {e['line']}: {e['name']} | Auth={e['auth']} | HTTPS={e['https']} | CORS={e['cors']}")
        else:
            print(f"ERROR: Missing assigned entry {name}")
            sys.exit(1)

    if malformed:
        print(f"WARNING: {len(malformed)} malformed rows encountered in category")

    print(f"Scanned {len(entries)} Music entries successfully (offline).")
    sys.exit(0)


if __name__ == "__main__":
    main()
