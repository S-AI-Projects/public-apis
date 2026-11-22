#!/usr/bin/env python3
"""
R02-T016: Offline test suite for Public APIs catalogue.
Category: Food & Drink [README.md]
Task: R02-T016 · 6 of 10

Selected entries:
- BaconMockup: https://baconmockup.com/ (Line 1220)
- CalorieNinjas: https://calorieninjas.com/api (Line 1221)
- Chomp: https://chompthis.com/api/ (Line 1222)
"""

import sys
import os
import re
import json
import socket
import argparse
from typing import List, Dict, Any, Tuple

SELECTED_ENTRIES = [
    {
        "name": "BaconMockup",
        "url": "https://baconmockup.com/",
        "line": 1220,
        "category": "Food & Drink",
        "raw": "| [BaconMockup](https://baconmockup.com/) | Resizable bacon placeholder images | No | Yes | Yes |"
    },
    {
        "name": "CalorieNinjas",
        "url": "https://calorieninjas.com/api",
        "line": 1221,
        "category": "Food & Drink",
        "raw": "| [CalorieNinjas](https://calorieninjas.com/api) | Nutrition and calorie data for foods and recipes | `apiKey` | Yes | Yes |"
    },
    {
        "name": "Chomp",
        "url": "https://chompthis.com/api/",
        "line": 1222,
        "category": "Food & Drink",
        "raw": "| [Chomp](https://chompthis.com/api/) | Data about various grocery products and foods | `apiKey` | Yes | Unknown |"
    }
]

def parse_food_entry(line: str) -> Dict[str, Any]:
    """
    Parses and validates a table row from Food & Drink.
    Works entirely offline without network access.
    """
    line = line.strip()
    if not line.startswith('|') or line.startswith('|---'):
        return {"valid": False, "error": "Not a table row"}
        
    parts = [p.strip() for p in line.split('|')[1:-1]]
    if len(parts) != 5:
        return {"valid": False, "error": f"Invalid segment count: expected 5, got {len(parts)}"}
        
    title_raw, desc, auth, https, cors = parts
    
    # Check title markdown syntax
    title_match = re.match(r'^\[([^\]]+)\]\((https?://[^\s)]+)\)$', title_raw)
    if not title_match:
        return {"valid": False, "error": "Malformed title/link syntax"}
        
    name, url = title_match.group(1), title_match.group(2)
    
    # Check unusual URL characters
    unusual_chars_present = any(ch in url for ch in ['%', '?', '&', '=', '~', '_', '-', ':'])
    
    # Check auth
    if auth != 'No' and not (auth.startswith('`') and auth.endswith('`')):
        return {"valid": False, "error": f"Auth value not enclosed in backticks: {auth}"}
        
    return {
        "valid": True,
        "name": name,
        "url": url,
        "description": desc,
        "auth": auth,
        "https": https,
        "cors": cors,
        "has_unusual_url_chars": unusual_chars_present,
        "error": None
    }

def get_fixtures() -> Dict[str, List[Dict[str, Any]]]:
    return {
        "valid_rows": [
            {
                "input": "| [BaconMockup](https://baconmockup.com/) | Resizable bacon placeholder images | No | Yes | Yes |",
                "expected_valid": True,
                "label": "Standard valid row"
            },
            {
                "input": "| [CalorieNinjas](https://calorieninjas.com/api) | Nutrition and calorie data for foods and recipes | `apiKey` | Yes | Yes |",
                "expected_valid": True,
                "label": "Valid row with apiKey"
            }
        ],
        "malformed_rows": [
            {
                "input": "| [BaconMockup](https://baconmockup.com/) | Resizable bacon placeholder images | No | Yes |",
                "expected_valid": False,
                "expected_error": "Invalid segment count",
                "label": "Missing column"
            },
            {
                "input": "| BaconMockup(https://baconmockup.com/) | Missing brackets | No | Yes | Yes |",
                "expected_valid": False,
                "expected_error": "Malformed title/link syntax",
                "label": "Malformed markdown link"
            },
            {
                "input": "| [Chomp](https://chompthis.com/api/) | Food data | apiKey | Yes | Unknown |",
                "expected_valid": False,
                "expected_error": "Auth value not enclosed in backticks",
                "label": "Auth missing backticks"
            }
        ],
        "unusual_url_rows": [
            {
                "input": "| [Percent URL](https://api.example.com/food%20drink?query=bacon&limit=10#section) | Handles percent encoding and queries | No | Yes | Yes |",
                "expected_valid": True,
                "expected_unusual": True,
                "label": "URL with percent encoding and query parameters"
            },
            {
                "input": "| [Port and Tilde](https://api.example.com:8080/~chef/recipe-api) | Handles ports, tilde and dashes | `apiKey` | Yes | Yes |",
                "expected_valid": True,
                "expected_unusual": True,
                "label": "URL with explicit port and tilde"
            }
        ]
    }

def block_network():
    """Patches socket to ensure no network calls occur during offline tests."""
    def guarded_socket(*args, **kwargs):
        raise RuntimeError("Network disabled: test must run purely offline!")
    socket.socket = guarded_socket

def run_self_test() -> bool:
    print("[*] Running R02-T016 self-test with network disabled...")
    block_network()
    
    fixtures = get_fixtures()
    
    # 1. Test valid rows
    for case in fixtures["valid_rows"]:
        res = parse_food_entry(case["input"])
        assert res["valid"] == case["expected_valid"], f"Failed valid test: {case['label']}"
        assert res["error"] is None
    print("  [PASS] Valid Food & Drink rows parsed correctly offline")
    
    # 2. Test malformed rows
    for case in fixtures["malformed_rows"]:
        res = parse_food_entry(case["input"])
        assert res["valid"] == case["expected_valid"], f"Malformed row unexpectedly passed: {case['label']}"
        assert case["expected_error"] in res["error"], f"Error mismatch: {res['error']}"
    print("  [PASS] Malformed rows rejected with explicit expected errors")
    
    # 3. Test unusual URL characters
    for case in fixtures["unusual_url_rows"]:
        res = parse_food_entry(case["input"])
        assert res["valid"] == case["expected_valid"], f"Unusual URL failed: {case['label']}"
        assert res["has_unusual_url_chars"] == case["expected_unusual"]
    print("  [PASS] Unusual URL characters (encoding, query, tilde, port) handled correctly")
    
    # 4. Verify selected catalogue entries
    for entry in SELECTED_ENTRIES:
        res = parse_food_entry(entry["raw"])
        assert res["valid"] is True, f"Failed on real entry: {entry['name']}"
    print("  [PASS] Selected catalogue entries (BaconMockup, CalorieNinjas, Chomp) verified offline")

    print("[+] All R02-T016 self-test assertions PASSED successfully in offline mode!")
    return True

def run_live():
    print("[*] Running optional live check on selected Food & Drink entries...")
    import urllib.request
    import ssl
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    
    for entry in SELECTED_ENTRIES:
        req = urllib.request.Request(entry["url"], headers={"User-Agent": "Mozilla/5.0"})
        try:
            with urllib.request.urlopen(req, context=ctx, timeout=5) as resp:
                print(f"  [OK] {entry['name']} -> HTTP {resp.status} ({resp.url})")
        except Exception as e:
            print(f"  [WARN] {entry['name']} -> {type(e).__name__}: {e} (Retaining link per policy)")

def main():
    parser = argparse.ArgumentParser(description="R02-T016 Offline Food & Drink Test Suite")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture test suite")
    parser.add_argument("--live", action="store_true", help="Optional live check of selected entries")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.live:
        run_live()
        sys.exit(0)

    # Default action
    run_self_test()

if __name__ == "__main__":
    main()
