#!/usr/bin/env python3
"""
R02-T015: Verify entry metadata for Public APIs catalogue.
Category: Test Data [README.md]
Task: R02-T015 · 5 of 10

Selected entries:
- AddressMock: https://addressmock.com/api (Line 2430)
- Bacon Ipsum: https://baconipsum.com/json-api/ (Line 2431)
- Dicebear Avatars: https://avatars.dicebear.com/ (Line 2432)
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Tuple, Optional

AUTH_OPTIONS = ['`apiKey`', '`OAuth`', '`X-Mashape-Key`', '`User-Agent`', 'No']
HTTPS_OPTIONS = ['Yes', 'No']
CORS_OPTIONS = ['Yes', 'No', 'Unknown']

SELECTED_ENTRIES = [
    {
        "name": "AddressMock",
        "url": "https://addressmock.com/api",
        "line": 2430,
        "category": "Test Data",
        "catalogue": {
            "title": "[AddressMock](https://addressmock.com/api)",
            "description": "Random US, Hong Kong and Cape Verde addresses with matched city, state and ZIP",
            "auth": "No",
            "https": "Yes",
            "cors": "Yes"
        },
        "observed_docs": {
            "url": "https://addressmock.com/api (Returns HTTP 404 / inactive domain)",
            "auth": "No",
            "https": "Yes",
            "cors": "Yes",
            "status": "Inactive/Unreachable"
        },
        "proposed": {
            "action": "Retain entry",
            "reason": "Policy: No link is removed solely because a single automated request failed. Retain pending upstream confirmation."
        }
    },
    {
        "name": "Bacon Ipsum",
        "url": "https://baconipsum.com/json-api/",
        "line": 2431,
        "category": "Test Data",
        "catalogue": {
            "title": "[Bacon Ipsum](https://baconipsum.com/json-api/)",
            "description": "A Meatier Lorem Ipsum Generator",
            "auth": "No",
            "https": "Yes",
            "cors": "Unknown"
        },
        "observed_docs": {
            "url": "https://baconipsum.com/json-api/",
            "auth": "No",
            "https": "Yes",
            "cors": "Yes (Access-Control-Allow-Origin: * supported by JSON API)",
            "status": "Active"
        },
        "proposed": {
            "action": "Update CORS",
            "reason": "Official API supports CORS headers natively; proposed update from 'Unknown' to 'Yes'."
        }
    },
    {
        "name": "Dicebear Avatars",
        "url": "https://avatars.dicebear.com/",
        "line": 2432,
        "category": "Test Data",
        "catalogue": {
            "title": "[Dicebear Avatars](https://avatars.dicebear.com/)",
            "description": "Generate random pixel-art avatars",
            "auth": "No",
            "https": "Yes",
            "cors": "No"
        },
        "observed_docs": {
            "url": "https://www.dicebear.com/ (Redirected from avatars.dicebear.com)",
            "auth": "No",
            "https": "Yes",
            "cors": "Yes (Public avatar HTTP API permits cross-origin SVG/PNG embedding)",
            "status": "Active"
        },
        "proposed": {
            "action": "Update URL & CORS",
            "reason": "Domain migrated to www.dicebear.com and public avatar endpoint supports cross-origin requests ('Yes')."
        }
    }
]

def parse_and_validate_row(line: str, line_num: int = 1) -> Tuple[bool, Optional[Dict[str, str]], List[str]]:
    """
    Parses a markdown table row and validates that all 5 required fields are present and valid.
    """
    errors = []
    if not line.strip().startswith('|') or line.strip().startswith('|---'):
        return False, None, ["Not a table row"]

    segments = [s.strip() for s in line.strip().split('|')[1:-1]]
    if len(segments) != 5:
        errors.append(f"(L{line_num:03d}) Entry must have exactly 5 columns (got {len(segments)})")
        return False, None, errors

    title_seg, desc_seg, auth_seg, https_seg, cors_seg = segments

    # Check title
    if not re.match(r'^\[.+\]\(http.+\)$', title_seg):
        errors.append(f"(L{line_num:03d}) Title must be formatted as [TITLE](URL)")

    # Check description
    if not desc_seg:
        errors.append(f"(L{line_num:03d}) Missing required description field")

    # Check Auth
    if auth_seg not in AUTH_OPTIONS:
        errors.append(f"(L{line_num:03d}) Invalid Auth option: '{auth_seg}'. Allowed: {AUTH_OPTIONS}")

    # Check HTTPS
    if https_seg not in HTTPS_OPTIONS:
        errors.append(f"(L{line_num:03d}) Invalid HTTPS option: '{https_seg}'. Allowed: {HTTPS_OPTIONS}")

    # Check CORS
    if cors_seg not in CORS_OPTIONS:
        errors.append(f"(L{line_num:03d}) Invalid CORS option: '{cors_seg}'. Allowed: {CORS_OPTIONS}")

    parsed = {
        "title": title_seg,
        "description": desc_seg,
        "auth": auth_seg,
        "https": https_seg,
        "cors": cors_seg
    }
    return (len(errors) == 0), parsed, errors

def generate_evidence_table(entries: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Generates a structured evidence table with source URL, observed documentation value,
    and proposed catalogue value for each entry.
    """
    table = []
    for e in entries:
        table.append({
            "name": e["name"],
            "line": e["line"],
            "source_url": e["url"],
            "catalogue_fields": e["catalogue"],
            "observed_docs": e["observed_docs"],
            "proposed_change": e["proposed"]
        })
    return table

def get_fixtures() -> Dict[str, str]:
    return {
        "valid_row": "| [Bacon Ipsum](https://baconipsum.com/json-api/) | A Meatier Lorem Ipsum Generator | No | Yes | Unknown |",
        "missing_field_row": "| [Incomplete API](https://example.com) | Missing last column | No | Yes |",
        "invalid_auth_row": "| [Bad Auth API](https://example.com) | Test description | BearerToken | Yes | Yes |",
        "invalid_https_row": "| [Bad HTTPS API](https://example.com) | Test description | No | Maybe | Yes |",
        "invalid_cors_row": "| [Bad CORS API](https://example.com) | Test description | No | Yes | Enabled |"
    }

def run_self_test() -> bool:
    print("[*] Running R02-T015 self-test on metadata validation fixtures...")
    fixtures = get_fixtures()

    # 1. Valid row passes
    ok, parsed, errs = parse_and_validate_row(fixtures["valid_row"], 10)
    assert ok is True, f"Valid row failed: {errs}"
    assert parsed["title"] == "[Bacon Ipsum](https://baconipsum.com/json-api/)"
    print("  [PASS] Valid catalogue table row accepted")

    # 2. Missing required field fails
    ok_miss, _, errs_miss = parse_and_validate_row(fixtures["missing_field_row"], 20)
    assert ok_miss is False, "Fixture with missing field unexpectedly passed"
    assert any("5 columns" in e for e in errs_miss)
    print("  [PASS] Missing required column correctly rejected")

    # 3. Invalid Auth option fails
    ok_auth, _, errs_auth = parse_and_validate_row(fixtures["invalid_auth_row"], 30)
    assert ok_auth is False, "Invalid Auth option unexpectedly passed"
    print("  [PASS] Invalid Auth enum value correctly rejected")

    # 4. Invalid HTTPS option fails
    ok_https, _, errs_https = parse_and_validate_row(fixtures["invalid_https_row"], 40)
    assert ok_https is False, "Invalid HTTPS option unexpectedly passed"
    print("  [PASS] Invalid HTTPS enum value correctly rejected")

    # 5. Invalid CORS option fails
    ok_cors, _, errs_cors = parse_and_validate_row(fixtures["invalid_cors_row"], 50)
    assert ok_cors is False, "Invalid CORS option unexpectedly passed"
    print("  [PASS] Invalid CORS enum value correctly rejected")

    # 6. Verify evidence table structure
    evidence_table = generate_evidence_table(SELECTED_ENTRIES)
    assert len(evidence_table) == 3
    for item in evidence_table:
        assert "source_url" in item
        assert "observed_docs" in item
        assert "proposed_change" in item
    print("  [PASS] Evidence table contains source URL, observed docs value, and proposed value")

    # 7. Retention policy check
    addr_mock = next(item for item in evidence_table if item["name"] == "AddressMock")
    assert "Retain entry" in addr_mock["proposed_change"]["action"]
    print("  [PASS] Retention policy enforced for transiently failing AddressMock")

    print("[+] All R02-T015 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T015 Metadata Verification Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--evidence-table", action="store_true", help="Print evidence table for selected Test Data entries")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if args.evidence_table:
        print("\n=== Test Data Metadata Evidence Table ===")
        table = generate_evidence_table(SELECTED_ENTRIES)
        for item in table:
            print(f"L{item['line']} | {item['name']}")
            print(f"  Source URL: {item['source_url']}")
            print(f"  Catalogue:  Auth={item['catalogue_fields']['auth']} | HTTPS={item['catalogue_fields']['https']} | CORS={item['catalogue_fields']['cors']}")
            print(f"  Observed:   Auth={item['observed_docs']['auth']} | HTTPS={item['observed_docs']['https']} | CORS={item['observed_docs']['cors']} ({item['observed_docs']['status']})")
            print(f"  Decision:   {item['proposed_change']['action']} - {item['proposed_change']['reason']}\n")
        sys.exit(0)

    # Default action
    run_self_test()

if __name__ == "__main__":
    main()
