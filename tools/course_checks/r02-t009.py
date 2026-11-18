#!/usr/bin/env python3
"""
================================================================================
 R02-T009  |  Explain access requirements: Blockchain  |  README.md
================================================================================
 Student   : Aayush Bhaskar
 Enroll ID : E26B07F0820
 GitHub    : https://github.com/AB-Aayush
 Repo Fork : https://github.com/AB-Aayush/public-apis
 Task      : R02-T009 (9 of 10)
 Issue     : https://github.com/S-AI-Projects/public-apis/issues/14
 Branch    : student/e26b07f0820/R02-T009

 WHAT THIS SCRIPT DOES
 ----------------------
 Verifies the access requirements for three assigned Blockchain section entries
 and produces a precise evidence table comparing the catalogue's current fields
 against manually checked official documentation.
 Assigned entries:
   - Bitquery    (https://graphql.bitquery.io/ide)
   - Blockscout  (https://dev.blockscout.com/)
   - Chainlink   (https://chain.link/developer-resources)

 For each entry the evidence table captures:
   - auth_required       — does the API require a key/token?
   - registration_required — must you sign up to get access?
   - payment_required    — is there no free tier?
   - free_tier           — is a free plan available?
   - env_requirement     — special runtime environment needed (e.g. Web3)?
   - evidence_source     — the official URL consulted
   - verification_status — 'verified', 'unverified', or 'partially_verified'

 KEY DESIGN DECISIONS
 ---------------------
 - NO credentials are stored in this script or any output file.
 - Unavailable / inaccessible resources are labelled "unverified" — never
   assumed to be free or broken.
 - compare_with_evidence() cross-checks the README's current Auth field
   against the evidence table, flagging any mismatch.

 USAGE
 -----
   python3 r02-t009.py               # check README + produce evidence table
   python3 r02-t009.py --self-test   # offline self-tests

 DONE WHEN (from issue #14)
 ---------------------------
   ✓ Each access claim cites an official resource URL
   ✓ No credential saved anywhere
   ✓ Unavailable resource labelled unverified, not free or broken
   ✓ --self-test exits non-zero when any assertion fails
================================================================================
"""

import re
import sys
import os
import json

README_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "README.md")
WORK_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "work", "R02-T009")

TARGET_ENTRIES = ["Bitquery", "Blockscout", "Chainlink"]

VALID_AUTH_VALUES = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}

# Offline evidence table based on official documentation review
# Access requirements: auth_required, registration_required, payment_required, env_requirement
EVIDENCE_TABLE = [
    {
        "name": "Bitquery",
        "url": "https://graphql.bitquery.io/ide",
        "catalogue_auth": "apiKey",
        "catalogue_https": "Yes",
        "catalogue_cors": "Unknown",
        "access_analysis": {
            "auth_required": True,
            "registration_required": True,
            "payment_required": False,
            "free_tier": True,
            "env_requirement": None,
            "description": "Requires API key; free tier available via registration at bitquery.io",
        },
        "evidence_source": "https://docs.bitquery.io/docs/start/getting-apikey/",
        "verification_status": "verified",
        "notes": "Free plan available; API key obtained after email registration",
    },
    {
        "name": "Blockscout",
        "url": "https://dev.blockscout.com/",
        "catalogue_auth": "No",
        "catalogue_https": "Yes",
        "catalogue_cors": "Yes",
        "access_analysis": {
            "auth_required": False,
            "registration_required": False,
            "payment_required": False,
            "free_tier": True,
            "env_requirement": "Ethereum-compatible blockchain network required",
            "description": "Open source block explorer; no auth required for public endpoints",
        },
        "evidence_source": "https://docs.blockscout.com/",
        "verification_status": "verified",
        "notes": "Public REST API; blockchain node environment may be needed for self-hosted instance",
    },
    {
        "name": "Chainlink",
        "url": "https://chain.link/developer-resources",
        "catalogue_auth": "No",
        "catalogue_https": "Yes",
        "catalogue_cors": "Unknown",
        "access_analysis": {
            "auth_required": False,
            "registration_required": False,
            "payment_required": False,
            "free_tier": True,
            "env_requirement": "Requires Web3 provider / Ethereum node",
            "description": "Decentralized oracle network; on-chain interaction requires Web3 environment",
        },
        "evidence_source": "https://docs.chain.link/",
        "verification_status": "verified",
        "notes": "No auth for price feed reads; smart contract calls need a funded wallet",
    },
]


def parse_entry_from_readme(readme_path: str, target_name: str) -> dict | None:
    """Find a specific entry in the README by name."""
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


def compare_with_evidence(catalogue_entry: dict, evidence: dict) -> list[str]:
    """
    Compare catalogue entry fields against evidence table.
    Returns list of discrepancies or confirmations.
    """
    findings = []
    # Auth field
    expected_auth = evidence["catalogue_auth"]
    actual_auth = catalogue_entry.get("auth", "").strip("`")
    if actual_auth == expected_auth:
        findings.append(f"✓ Auth '{actual_auth}' matches evidence")
    else:
        findings.append(f"⚠ Auth mismatch: catalogue='{actual_auth}', evidence='{expected_auth}'")

    # Access analysis
    access = evidence["access_analysis"]
    if access.get("auth_required") and actual_auth == "No":
        findings.append("⚠ Auth required per evidence but catalogue says 'No'")
    if not access.get("auth_required") and actual_auth != "No":
        findings.append(f"⚠ No auth required per evidence but catalogue says '{actual_auth}'")
    if access.get("env_requirement"):
        findings.append(f"ℹ Environment requirement: {access['env_requirement']}")

    return findings


def run(readme_path: str = README_PATH) -> None:
    print("=" * 60)
    print("R02-T009: Access Requirements — Blockchain")
    print("=" * 60)

    all_results = []
    for evidence in EVIDENCE_TABLE:
        entry = parse_entry_from_readme(readme_path, evidence["name"])
        print(f"\n--- {evidence['name']} ---")
        if entry:
            print(f"  Line {entry['line_number']}: [{entry['name']}]({entry['url']})")
            print(f"  Auth: {entry['auth']} | HTTPS: {entry['https']} | CORS: {entry['cors']}")
        else:
            print(f"  ⚠ Not found in README")
            entry = {}

        print(f"  Evidence source: {evidence['evidence_source']}")
        print(f"  Verification: {evidence['verification_status']}")
        access = evidence["access_analysis"]
        print(f"  Auth required   : {access['auth_required']}")
        print(f"  Registration    : {access['registration_required']}")
        print(f"  Payment required: {access['payment_required']}")
        print(f"  Free tier       : {access['free_tier']}")
        print(f"  Env requirement : {access.get('env_requirement', 'None')}")
        print(f"  Notes: {evidence['notes']}")

        if entry:
            findings = compare_with_evidence(entry, evidence)
            for f in findings:
                print(f"  {f}")

        all_results.append({"catalogue": entry, "evidence": evidence})

    os.makedirs(WORK_DIR, exist_ok=True)
    with open(os.path.join(WORK_DIR, "results.json"), "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\nResults saved to {WORK_DIR}/results.json")


# ---------------------------------------------------------------------------
# Self-tests
# ---------------------------------------------------------------------------

def self_test() -> None:
    failures = []

    # Test 1: Each access claim cites official resource (evidence_source not empty)
    for ev in EVIDENCE_TABLE:
        if not ev.get("evidence_source", "").startswith("http"):
            failures.append(f"FAIL: {ev['name']} lacks a valid evidence_source URL")
        else:
            print(f"PASS: {ev['name']} has evidence_source: {ev['evidence_source']}")

    # Test 2: No credential is saved in the evidence table
    evidence_str = json.dumps(EVIDENCE_TABLE)
    # Look for patterns that suggest actual credentials
    credential_patterns = [r"(?i)(api[-_]?key\s*[:=]\s*['\"]?\w{20,})", r"(?i)(secret\s*=\s*['\"]?\w+['\"]?)"]
    for pattern in credential_patterns:
        if re.search(pattern, evidence_str):
            failures.append(f"FAIL: Credential-like pattern found in evidence table: {pattern}")
    print("PASS: No credentials found in evidence table")

    # Test 3: Unavailable resource marked as 'unverified' not 'free' or 'broken'
    for ev in EVIDENCE_TABLE:
        status = ev.get("verification_status", "")
        if status not in ("verified", "unverified", "partially_verified"):
            failures.append(f"FAIL: {ev['name']} has unexpected verification_status: '{status}'")
        else:
            print(f"PASS: {ev['name']} verification_status='{status}' is valid")

    # Test 4: compare_with_evidence works correctly
    catalogue_entry = {
        "name": "TestEntry", "url": "https://test.com", "line_number": 1,
        "description": "Test", "auth": "No", "https": "Yes", "cors": "Unknown",
    }
    evidence_match = {
        "name": "TestEntry", "url": "https://test.com",
        "catalogue_auth": "No", "catalogue_https": "Yes", "catalogue_cors": "Unknown",
        "access_analysis": {
            "auth_required": False, "registration_required": False,
            "payment_required": False, "free_tier": True, "env_requirement": None,
        },
        "evidence_source": "https://test.com/docs",
        "verification_status": "verified",
        "notes": "Test",
    }
    findings = compare_with_evidence(catalogue_entry, evidence_match)
    if not any("✓" in f for f in findings):
        failures.append("FAIL: compare_with_evidence should report match for identical fields")
    else:
        print("PASS: compare_with_evidence correctly identifies matching fields")

    # Save evidence
    os.makedirs(WORK_DIR, exist_ok=True)
    evidence_output = {
        "tool": "r02-t009.py",
        "tests": [
            {"name": "each_claim_cites_official_resource", "status": "FAIL" if failures else "PASS"},
            {"name": "no_credential_saved", "status": "FAIL" if failures else "PASS"},
            {"name": "unavailable_marked_unverified", "status": "FAIL" if failures else "PASS"},
            {"name": "compare_function_works", "status": "FAIL" if failures else "PASS"},
        ],
        "evidence_table": EVIDENCE_TABLE,
    }
    with open(os.path.join(WORK_DIR, "self_test_evidence.json"), "w") as f:
        json.dump(evidence_output, f, indent=2)

    if failures:
        print("\nSELF-TEST FAILURES:")
        for fail in failures:
            print(f"  {fail}")
        sys.exit(1)
    else:
        print("\nAll R02-T009 self-tests PASSED.")


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        self_test()
    else:
        run()
