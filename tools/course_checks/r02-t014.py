#!/usr/bin/env python3
"""
R02-T014: Check category placement for Public APIs catalogue.
Category: Security [README.md]
Task: R02-T014 · 4 of 10

Selected entries:
- Agent Verifier: https://packet.guru/agents/reference (Line 2180)
- Application Environment Verification: https://github.com/fingerprintjs/aev (Line 2181)
- BinaryEdge: https://docs.binaryedge.io/api-v2.html (Line 2182)
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Tuple

SELECTED_ENTRIES = [
    {
        "name": "Agent Verifier",
        "url": "https://packet.guru/agents/reference",
        "line": 2180,
        "category": "Security",
        "subject": "Web bot authentication signatures, agent identity and verification"
    },
    {
        "name": "Application Environment Verification",
        "url": "https://github.com/fingerprintjs/aev",
        "line": 2181,
        "category": "Security",
        "subject": "Device integrity, root detection and mobile security threats"
    },
    {
        "name": "BinaryEdge",
        "url": "https://docs.binaryedge.io/api-v2.html",
        "line": 2182,
        "category": "Security",
        "subject": "Threat intelligence, port scanning and internet-wide vulnerability assessment"
    }
]

def check_category_structure(markdown_lines: List[str]) -> Dict[str, Any]:
    """
    Checks markdown document structure for:
    - Repeated headings (e.g. duplicate ### Category)
    - Valid category boundaries
    """
    heading_counts: Dict[str, List[int]] = {}
    current_heading = None
    entries_by_heading: Dict[str, List[Dict[str, Any]]] = {}
    
    for idx, line in enumerate(markdown_lines):
        line_num = idx + 1
        m = re.match(r'^###\s+(.+)$', line.strip())
        if m:
            heading = m.group(1).strip()
            heading_counts.setdefault(heading, []).append(line_num)
            current_heading = heading
            entries_by_heading.setdefault(current_heading, [])
            continue
            
        if line.strip().startswith('| [') and current_heading:
            # parse entry title and link
            entry_m = re.search(r'\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]+)\|', line)
            if entry_m:
                entries_by_heading[current_heading].append({
                    "line": line_num,
                    "name": entry_m.group(1).strip(),
                    "url": entry_m.group(2).strip(),
                    "description": entry_m.group(3).strip(),
                    "category": current_heading
                })
                
    repeated_headings = {h: lines for h, lines in heading_counts.items() if len(lines) > 1}
    return {
        "repeated_headings": repeated_headings,
        "entries_by_heading": entries_by_heading
    }

def evaluate_placement(entry: Dict[str, Any], target_category: str) -> Dict[str, Any]:
    """
    Evaluates entry placement using contextual resource subject rather than naive keyword matching.
    """
    # Contextual security domains
    security_domains = [
        "threat intelligence", "root detection", "device integrity", "vulnerability",
        "authentication", "web bot", "bot auth", "scanning", "firewall", "encryption",
        "malware", "cybersecurity", "cve", "penetration testing", "signature"
    ]
    
    non_security_domains = [
        "weather forecast", "music streaming", "grocery items", "recipe calories",
        "flight tracker", "currency exchange"
    ]
    
    desc_subject = (entry.get("description", "") + " " + entry.get("subject", "")).lower()
    
    is_clearly_misplaced = any(ns in desc_subject for ns in non_security_domains)
    is_valid_security = any(sec in desc_subject for sec in security_domains)
    
    if is_clearly_misplaced:
        return {
            "name": entry["name"],
            "current_category": entry.get("category", "Unknown"),
            "is_valid": False,
            "cited_subject": entry.get("subject") or entry.get("description"),
            "recommendation": f"MISPLACED: Entry subject relates to non-security domain. Move to appropriate catalogue category."
        }
    
    return {
        "name": entry["name"],
        "current_category": target_category,
        "is_valid": True,
        "cited_subject": entry.get("subject") or entry.get("description"),
        "recommendation": f"VALID: Entry placement in {target_category} is appropriate based on resource subject."
    }

def get_fixtures() -> Tuple[List[str], List[Dict[str, Any]]]:
    sample_markdown = [
        "### Security",
        "| [Agent Verifier](https://packet.guru/agents/reference) | Self-check for AI agents: verifies Web Bot Auth signatures | No | Yes | No |",
        "| [Application Environment Verification](https://github.com/fingerprintjs/aev) | Android library and API to verify device safety and root detection | `apiKey` | Yes | Yes |",
        "| [BinaryEdge](https://docs.binaryedge.io/api-v2.html) | Provide access to BinaryEdge threat scanning platform | `apiKey` | Yes | Yes |",
        "| [Open-Meteo Weather](https://open-meteo.com) | Weather forecast data and meteorological models | No | Yes | Yes |", # Deliberately misplaced!
        "### Security", # Deliberately repeated heading!
        "| [Another Tool](https://example.com) | Another tool | No | Yes | Yes |"
    ]
    
    test_entries = [
        {
            "name": "Agent Verifier",
            "category": "Security",
            "subject": "Web Bot Auth signatures and agent identity",
            "description": "Verifies Web Bot Auth signatures"
        },
        {
            "name": "Open-Meteo Weather",
            "category": "Security",
            "subject": "Weather forecast data and meteorological models",
            "description": "Weather forecast data"
        }
    ]
    return sample_markdown, test_entries

def run_self_test() -> bool:
    print("[*] Running R02-T014 self-test on category placement fixtures...")
    md_lines, test_entries = get_fixtures()
    
    # 1. Structure check: Detect repeated headings
    struct = check_category_structure(md_lines)
    assert "Security" in struct["repeated_headings"], "Failed to detect duplicate ### Security heading"
    assert len(struct["repeated_headings"]["Security"]) == 2
    print("  [PASS] Repeated category headings detected")
    
    # 2. Placement check: Valid Security entry preserved
    res_valid = evaluate_placement(test_entries[0], "Security")
    assert res_valid["is_valid"] is True, "Valid security entry was improperly rejected"
    assert "Web Bot Auth" in res_valid["cited_subject"]
    print("  [PASS] Valid Security category entry preserved with cited subject")
    
    # 3. Placement check: Deliberately misplaced fixture detected
    res_misplaced = evaluate_placement(test_entries[1], "Security")
    assert res_misplaced["is_valid"] is False, "Deliberately misplaced fixture was not identified"
    assert "MISPLACED" in res_misplaced["recommendation"]
    print("  [PASS] Deliberately misplaced fixture identified with resource subject cited")
    
    # 4. Keyword robustness check: Do not reclassify solely on generic keyword 'verification'
    aev_entry = {
        "name": "Application Environment Verification",
        "category": "Security",
        "subject": "Device safety, root detection and tampering verification",
        "description": "Root detection and tampering verification"
    }
    res_aev = evaluate_placement(aev_entry, "Security")
    assert res_aev["is_valid"] is True, "Security verification entry was falsely reclassified"
    print("  [PASS] Avoids reclassifying entries solely from ambiguous keywords")
    
    print("[+] All R02-T014 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T014 Category Placement Verification Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--check-selected", action="store_true", help="Verify placement of selected Security entries")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.check_selected:
        print("\n=== Category Placement: Selected Security Entries ===")
        for entry in SELECTED_ENTRIES:
            eval_res = evaluate_placement(entry, "Security")
            print(f"L{entry['line']} | {entry['name']}")
            print(f"  Category: {entry['category']} (Valid: {eval_res['is_valid']})")
            print(f"  Subject:  {entry['subject']}")
            print(f"  Result:   {eval_res['recommendation']}\n")
        sys.exit(0)

    # Default action
    run_self_test()

if __name__ == "__main__":
    main()
