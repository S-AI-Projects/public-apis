#!/usr/bin/env python3
"""
R02-T018: Explain access requirements for Public APIs catalogue.
Category: Text Analysis [README.md]
Task: R02-T018 · 8 of 10

Selected entries:
- Code Detection: https://codedetectionapi.runtime.dev (Line 2474)
- apilayer languagelayer: https://languagelayer.com/ (Line 2475)
- Aylien Text Analysis: https://docs.aylien.com/textapi/#getting-started (Line 2476)
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Optional

SELECTED_ENTRIES = [
    {
        "name": "Code Detection",
        "url": "https://codedetectionapi.runtime.dev",
        "line": 2474,
        "category": "Text Analysis",
        "catalogue_auth": "`OAuth`",
        "official_citation": "https://codedetectionapi.runtime.dev",
        "status": "unavailable",
        "access_label": "unverified",
        "notes": "Domain presented TLS handshake failure during live probe. Resource must be labelled unverified rather than broken or free."
    },
    {
        "name": "apilayer languagelayer",
        "url": "https://languagelayer.com/",
        "line": 2475,
        "category": "Text Analysis",
        "catalogue_auth": "`OAuth`",
        "official_citation": "https://languagelayer.com/documentation",
        "status": "available",
        "access_label": "verified",
        "access_model": "Registration required. Uses API Access Key (`apiKey`) passed as 'access_key' query parameter; free tier with monthly request quota.",
        "proposed_correction": "Update Auth from `OAuth` to `apiKey`"
    },
    {
        "name": "Aylien Text Analysis",
        "url": "https://docs.aylien.com/textapi/#getting-started",
        "line": 2476,
        "category": "Text Analysis",
        "catalogue_auth": "`apiKey`",
        "official_citation": "https://docs.aylien.com/textapi/#getting-started",
        "status": "unavailable",
        "access_label": "unverified",
        "notes": "Legacy docs endpoint unreachable via DNS. Resource must be labelled unverified rather than broken or free."
    }
]

def audit_access_claims(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Audits access claims to verify:
    - Every claim cites official resource documentation.
    - Unavailable resources are labelled 'unverified' rather than 'free' or 'broken'.
    - No secret credentials, passwords, or personal API keys are persisted.
    """
    credential_patterns = [
        re.compile(r'(?:api[_-]?key|secret|token|password|auth[_-]?token)\s*[:=]\s*["\']?[a-zA-Z0-9_\-]{16,}', re.I)
    ]
    
    audited = []
    for entry in entries:
        citation = entry.get("official_citation")
        has_citation = bool(citation and citation.startswith("http"))
        
        status = entry.get("status")
        access_label = entry.get("access_label")
        
        # Enforce that unavailable resources are labelled 'unverified'
        if status == "unavailable":
            correct_label = (access_label == "unverified")
        else:
            correct_label = True
            
        # Check for leaked credentials in notes, description, or fields
        content_dump = json.dumps(entry)
        has_credential_leak = any(pat.search(content_dump) for pat in credential_patterns)
        
        audited.append({
            "name": entry["name"],
            "line": entry.get("line"),
            "has_citation": has_citation,
            "correct_label": correct_label,
            "has_credential_leak": has_credential_leak,
            "access_label": access_label,
            "citation": citation
        })
        
    return {
        "all_cited": all(a["has_citation"] for a in audited),
        "all_labels_valid": all(a["correct_label"] for a in audited),
        "no_credentials_saved": not any(a["has_credential_leak"] for a in audited),
        "entries": audited
    }

def get_fixtures() -> List[Dict[str, Any]]:
    return [
        {
            "name": "Fixture Active Service",
            "url": "https://api.example.com",
            "official_citation": "https://api.example.com/docs/auth",
            "status": "available",
            "access_label": "verified",
            "access_model": "API Key registration required"
        },
        {
            "name": "Fixture Unavailable Service",
            "url": "https://down.example.com",
            "official_citation": "https://down.example.com/docs",
            "status": "unavailable",
            "access_label": "unverified",
            "access_model": "Temporarily unreachable; labelled unverified"
        },
        {
            "name": "Fixture Missing Citation (Bad)",
            "url": "https://nocite.example.com",
            "official_citation": "",
            "status": "available",
            "access_label": "verified"
        },
        {
            "name": "Fixture Improperly Labeled (Bad)",
            "url": "https://down2.example.com",
            "official_citation": "https://down2.example.com",
            "status": "unavailable",
            "access_label": "broken" # Must NOT be labelled 'broken' or 'free'
        }
    ]

def run_self_test() -> bool:
    print("[*] Running R02-T018 self-test on access requirements verification...")
    fixtures = get_fixtures()
    
    # 1. Audit selected real entries
    real_audit = audit_access_claims(SELECTED_ENTRIES)
    assert real_audit["all_cited"] is True, "Not all selected entries cite official resources"
    assert real_audit["all_labels_valid"] is True, "Unavailable entries must be labelled 'unverified'"
    assert real_audit["no_credentials_saved"] is True, "Credentials detected in entry record!"
    print("  [PASS] Selected entries cite official resources with unverified labeling for offline hosts")
    print("  [PASS] Zero credentials saved in repository records")

    # 2. Test Fixture: Missing citation correctly caught
    res_fixtures = audit_access_claims(fixtures)
    assert res_fixtures["all_cited"] is False, "Missing citation fixture was not flagged"
    print("  [PASS] Missing official citation fixture correctly identified")

    # 3. Test Fixture: Improper label ('broken' instead of 'unverified') correctly caught
    assert res_fixtures["all_labels_valid"] is False, "Improper label fixture ('broken') was not flagged"
    print("  [PASS] Improper label ('broken' instead of 'unverified') correctly rejected")

    # 4. Test Credential Leak Detection
    leaked_entry = [{
        "name": "Leak API",
        "url": "https://leak.example.com",
        "official_citation": "https://leak.example.com/docs",
        "status": "available",
        "access_label": "verified",
        "notes": "Used api_key=ab12cd34ef56gh78ij90 to test"
    }]
    leak_audit = audit_access_claims(leaked_entry)
    assert leak_audit["no_credentials_saved"] is False, "Credential leak was not caught"
    print("  [PASS] Credential security guard verified")

    print("[+] All R02-T018 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T018 Access Requirements Verifier")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--audit", action="store_true", help="Audit selected Text Analysis entries")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)

    if args.audit:
        print("\n=== Text Analysis Access Requirements Audit ===")
        for e in SELECTED_ENTRIES:
            print(f"L{e['line']} | {e['name']}: {e['url']}")
            print(f"  Official Citation: {e['official_citation']}")
            print(f"  Status: {e['status']} | Access Label: {e['access_label']}")
            if "proposed_correction" in e:
                print(f"  Correction: {e['proposed_correction']}")
            print(f"  Notes: {e.get('notes', e.get('access_model'))}\n")
        sys.exit(0)

    run_self_test()

if __name__ == "__main__":
    main()
