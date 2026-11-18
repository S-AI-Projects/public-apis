#!/usr/bin/env python3
"""
R02-T044: Verify entry metadata: Cryptocurrency [README.md]
Validates the table format, required fields, and metadata for the selected entries:
  - Coinlayer: https://coinlayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers
  - 0x: https://docs.0x.org/
  - 1inch: https://business.1inch.com/portal/documentation
"""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"
CATEGORY = "Cryptocurrency"

EXPECTED_ENTRIES = {
    "Coinlayer": {
        "url": "https://coinlayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers",
        "auth": "`apiKey`",
        "https": "Yes",
        "cors": "Unknown",
    },
    "0x": {
        "url": "https://docs.0x.org/",
        "auth": "No",
        "https": "Yes",
        "cors": "Yes",
    },
    "1inch": {
        "url": "https://business.1inch.com/portal/documentation",
        "auth": "`apiKey`",
        "https": "Yes",
        "cors": "Unknown",
    },
}

LINK_PATTERN = re.compile(r"^\s*\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|(.*)\|\s*$")


def parse_cryptocurrency_entries(file_path):
    """Parses and validates table structure and entry metadata in Cryptocurrency section."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    header_found = False
    entries = {}
    errors = []

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("### "):
            cat = stripped[4:].strip()
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
        if re.match(r"^\|?\s*:?-+:?\s*(\|:?-+:?\s*)+\|?$", stripped):
            continue

        if not stripped.startswith("|") or not stripped.endswith("|"):
            continue

        # Parse table cells
        cells = [c.strip() for c in stripped[1:-1].split("|")]
        if len(cells) < 5:
            errors.append(f"Line {idx}: Malformed row, expected 5 columns, found {len(cells)}")
            continue

        # Check required fields
        api_cell, desc, auth, https, cors = cells[0], cells[1], cells[2], cells[3], cells[4]
        if not desc:
            errors.append(f"Line {idx}: Missing required description field")
        if not auth:
            errors.append(f"Line {idx}: Missing required Auth field")
        if not https:
            errors.append(f"Line {idx}: Missing required HTTPS field")
        if not cors:
            errors.append(f"Line {idx}: Missing required CORS field")

        link_match = re.search(r"\[([^\]]+)\]\(([^)]+)\)", api_cell)
        if not link_match:
            errors.append(f"Line {idx}: API cell does not contain a valid Markdown link: '{api_cell}'")
            continue

        name = link_match.group(1).strip()
        url = link_match.group(2).strip()

        entries[name] = {
            "name": name,
            "url": url,
            "description": desc,
            "auth": auth,
            "https": https,
            "cors": cors,
            "line": idx,
        }

    return entries, errors


def check_metadata(entries, errors):
    """Validate assigned entries against expected metadata."""
    validation_errors = list(errors)
    for name, expected in EXPECTED_ENTRIES.items():
        if name not in entries:
            validation_errors.append(f"Missing required entry: {name}")
            continue

        actual = entries[name]
        if actual["url"] != expected["url"]:
            validation_errors.append(f"URL mismatch for {name}: expected '{expected['url']}', got '{actual['url']}' (Line {actual['line']})")
        if actual["auth"] != expected["auth"]:
            validation_errors.append(f"Auth mismatch for {name}: expected '{expected['auth']}', got '{actual['auth']}' (Line {actual['line']})")
        if actual["https"] != expected["https"]:
            validation_errors.append(f"HTTPS mismatch for {name}: expected '{expected['https']}', got '{actual['https']}' (Line {actual['line']})")
        if actual["cors"] != expected["cors"]:
            validation_errors.append(f"CORS mismatch for {name}: expected '{expected['cors']}', got '{actual['cors']}' (Line {actual['line']})")

    return validation_errors


def run_self_tests():
    """Deterministic offline test suite verifying success and failure cases."""
    try:
        assert False
        print("ERROR: assertions disabled (python -O/-OO); refusing false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    fixtures_dir = ROOT / "work" / "R02-T044" / "fixtures"

    # 1. Valid fixture
    entries, errors = parse_cryptocurrency_entries(fixtures_dir / "valid.md")
    val_errors = check_metadata(entries, errors)
    assert not val_errors, f"Valid fixture failed: {val_errors}"
    assert len(entries) == 3

    # 2. Missing required field (description missing)
    entries, errors = parse_cryptocurrency_entries(fixtures_dir / "missing-required-field.md")
    val_errors = check_metadata(entries, errors)
    assert any("Missing required" in e for e in val_errors), "Missing required field was not detected"

    # 3. Wrong metadata fixture
    entries, errors = parse_cryptocurrency_entries(fixtures_dir / "wrong-metadata.md")
    val_errors = check_metadata(entries, errors)
    assert any("CORS mismatch" in e or "Auth mismatch" in e for e in val_errors), "Wrong metadata was not detected"

    # 4. Malformed row fixture
    entries, errors = parse_cryptocurrency_entries(fixtures_dir / "malformed-row.md")
    val_errors = check_metadata(entries, errors)
    assert any("Malformed row" in e for e in val_errors), "Malformed row was not detected"

    # Record actual results
    work_dir = ROOT / "work" / "R02-T044"
    work_dir.mkdir(parents=True, exist_ok=True)
    with open(work_dir / "actual-results.json", "w", encoding="utf-8") as f:
        json.dump({"self_test": "passed", "fixtures_passed": 4}, f, indent=2)

    print("Self-test passed: 4 fixture checks (valid, missing-field, wrong-metadata, malformed-row).")


def main():
    parser = argparse.ArgumentParser(description="Cryptocurrency entry metadata checker")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture checks")
    parser.add_argument("--readme", type=str, default=None, help="Path to markdown file")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    target_file = Path(args.readme) if args.readme else README
    entries, errors = parse_cryptocurrency_entries(target_file)
    val_errors = check_metadata(entries, errors)

    for name in EXPECTED_ENTRIES:
        if name in entries:
            e = entries[name]
            print(f"OK line {e['line']}: {e['name']} | Auth={e['auth']} | HTTPS={e['https']} | CORS={e['cors']}")

    if val_errors:
        for err in val_errors:
            print(f"ERROR: {err}")
        sys.exit(1)

    print("OK: Cryptocurrency table structure valid; all selected entries match expected metadata.")
    sys.exit(0)


if __name__ == "__main__":
    main()
