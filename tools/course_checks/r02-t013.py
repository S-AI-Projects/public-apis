#!/usr/bin/env python3
"""
R02-T013: Detect probable duplicates in Public APIs catalogue.
Category: Phone [README.md]
Task: R02-T013 · 3 of 10

Selected entries:
- Numlookup: https://numlookupapi.com (Line 2040)
- Numverify: https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers (Line 2041)
- Cloudmersive Validate: https://cloudmersive.com/phone-number-validation-API (Line 2042)
"""

import sys
import os
import re
import json
import argparse
import urllib.parse
from typing import List, Dict, Any, Tuple, Set

SELECTED_ENTRIES = [
    {
        "name": "Numlookup",
        "url": "https://numlookupapi.com",
        "line": 2040,
        "category": "Phone"
    },
    {
        "name": "Numverify",
        "url": "https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers",
        "line": 2041,
        "category": "Phone"
    },
    {
        "name": "Cloudmersive Validate",
        "url": "https://cloudmersive.com/phone-number-validation-API",
        "line": 2042,
        "category": "Phone"
    }
]

def normalize_url_conservative(raw_url: str) -> str:
    """
    Performs conservative URL normalization:
    - Lowercase scheme and netloc.
    - Strips default port (:80 for http, :443 for https).
    - Removes duplicate slashes in path, strips trailing slash if bare root.
    - CRITICAL: Preserves query parameters and fragments intact!
    """
    parsed = urllib.parse.urlsplit(raw_url.strip())
    scheme = parsed.scheme.lower()
    netloc = parsed.netloc.lower()
    
    # Remove default ports
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    elif scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]
        
    path = parsed.path
    if path == "/":
        path = ""
    elif path.endswith("/") and len(path) > 1:
        path = path.rstrip("/")
        
    # Reconstruct preserving exact query and fragment
    return urllib.parse.urlunsplit((scheme, netloc, path, parsed.query, parsed.fragment))

def group_duplicate_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Groups entries by exact URL and conservative normalized URL.
    Identifies exact duplicates and near-duplicates while keeping distinct query/anchor resources separate.
    """
    exact_map: Dict[str, List[Dict[str, Any]]] = {}
    norm_map: Dict[str, List[Dict[str, Any]]] = {}
    
    for entry in entries:
        raw = entry["url"].strip()
        exact_map.setdefault(raw, []).append(entry)
        
        norm = normalize_url_conservative(raw)
        norm_map.setdefault(norm, []).append(entry)
        
    exact_duplicates = [group for group in exact_map.values() if len(group) > 1]
    norm_duplicates = [group for group in norm_map.values() if len(group) > 1]
    
    # Formulate recommendations requiring manual review pairs
    proposed_actions = []
    for group in norm_duplicates:
        names = [e["name"] for e in group]
        lines = [e.get("line", "?") for e in group]
        proposed_actions.append({
            "group": names,
            "lines": lines,
            "urls": [e["url"] for e in group],
            "requires_manual_review": True,
            "recommendation": f"Potential duplicate between lines {lines}. Requires manual confirmation before deletion."
        })
        
    return {
        "exact_duplicates": exact_duplicates,
        "normalized_duplicates": norm_duplicates,
        "proposed_actions": proposed_actions
    }

def get_fixtures() -> List[Dict[str, Any]]:
    return [
        # Pair 1: Exact duplicates
        {"name": "API One", "url": "https://api.example.com/v1", "line": 10},
        {"name": "API One Clone", "url": "https://api.example.com/v1", "line": 25},
        
        # Pair 2: Conservative normalization match (casing, default port, trailing slash)
        {"name": "Upper Host", "url": "https://API.SAMPLE.COM:443/docs/", "line": 30},
        {"name": "Lower Host", "url": "https://api.sample.com/docs", "line": 35},
        
        # Distinct query parameters (Must NOT be merged)
        {"name": "Base URL", "url": "https://numverify.com", "line": 40},
        {"name": "Campaign URL", "url": "https://numverify.com?utm_source=Github", "line": 45},
        
        # Distinct fragments/anchors (Must NOT be merged)
        {"name": "Docs Section A", "url": "https://example.com/docs#phone", "line": 50},
        {"name": "Docs Section B", "url": "https://example.com/docs#email", "line": 55},
        
        # Distinct paths (Must NOT be merged)
        {"name": "Cloudmersive Validate Phone", "url": "https://cloudmersive.com/phone-number-validation-API", "line": 2042},
        {"name": "Cloudmersive Validate General", "url": "https://cloudmersive.com/validate-api", "line": 988}
    ]

def run_self_test() -> bool:
    print("[*] Running R02-T013 self-test on duplicate detection fixtures...")
    fixtures = get_fixtures()
    results = group_duplicate_entries(fixtures)
    
    # 1. Exact duplicates found
    exact_groups = results["exact_duplicates"]
    assert len(exact_groups) >= 1, "Expected exact duplicates to be detected"
    exact_names = [e["name"] for e in exact_groups[0]]
    assert "API One" in exact_names and "API One Clone" in exact_names
    print("  [PASS] Exact duplicates identified")
    
    # 2. Conservative normalization matches (case and port)
    norm_groups = results["normalized_duplicates"]
    norm_group_found = False
    for g in norm_groups:
        names = [e["name"] for e in g]
        if "Upper Host" in names and "Lower Host" in names:
            norm_group_found = True
            break
    assert norm_group_found, "Conservative normalization failed to match case/port variance"
    print("  [PASS] Conservative normalization matches detected")
    
    # 3. Query parameters kept distinct
    for g in norm_groups:
        names = [e["name"] for e in g]
        assert not ("Base URL" in names and "Campaign URL" in names), \
            "Query parameter variants were erroneously merged!"
    print("  [PASS] Distinct query parameters preserved as separate resources")
    
    # 4. Distinct fragments kept distinct
    for g in norm_groups:
        names = [e["name"] for e in g]
        assert not ("Docs Section A" in names and "Docs Section B" in names), \
            "Distinct URL fragments were erroneously merged!"
    print("  [PASS] Distinct URL anchors preserved as separate resources")
    
    # 5. Distinct paths kept distinct
    for g in norm_groups:
        names = [e["name"] for e in g]
        assert not ("Cloudmersive Validate Phone" in names and "Cloudmersive Validate General" in names), \
            "Distinct API endpoint paths were erroneously merged!"
    print("  [PASS] Distinct API paths preserved")
    
    # 6. Manual review required for proposed deletions
    for action in results["proposed_actions"]:
        assert action["requires_manual_review"] is True
    print("  [PASS] Every proposed deletion requires a manually reviewed pair")
    
    print("[+] All R02-T013 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T013 Duplicate Detection Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--check-selected", action="store_true", help="Analyze selected Phone entries")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.check_selected:
        print("\n=== Analyzing Selected Phone Entries ===")
        results = group_duplicate_entries(SELECTED_ENTRIES)
        print(f"Total entries analyzed: {len(SELECTED_ENTRIES)}")
        print(f"Exact duplicates found: {len(results['exact_duplicates'])}")
        print(f"Normalized duplicates found: {len(results['normalized_duplicates'])}")
        for entry in SELECTED_ENTRIES:
            print(f"L{entry['line']} | {entry['name']}: {entry['url']}")
        print("\nConclusion: Selected Phone entries represent distinct endpoints. No duplicate removal warranted.")
        sys.exit(0)

    # Default action
    run_self_test()

if __name__ == "__main__":
    main()
