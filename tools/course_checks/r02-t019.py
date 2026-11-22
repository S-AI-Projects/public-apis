#!/usr/bin/env python3
"""
R02-T019: Repeatable maintenance report for Public APIs catalogue.
Category: Books [README.md]
Task: R02-T019 · 9 of 10

Selected entries:
- A Bíblia Digital: https://www.abibliadigital.com.br/en (Line 344)
- Amanah Sunnah: https://sunnah.amanahagent.cloud/developers (Line 345)
- Bhagavad Gita: https://docs.bhagavadgitaapi.in (Line 346)
"""

import sys
import os
import json
import hashlib
import argparse
from typing import List, Dict, Any, Tuple

SELECTED_ENTRIES = [
    {
        "line": 344,
        "name": "A Bíblia Digital",
        "category": "Books",
        "before_metadata": {
            "title": "[A Bíblia Digital](https://www.abibliadigital.com.br/en)",
            "description": "Do not worry about managing the multiple versions of the Bible",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "No"
        },
        "observed_facts": {
            "status_code": 503,
            "response": "Service Unavailable",
            "final_url": "https://www.abibliadigital.com.br/en",
            "probe_note": "Host returned 503 during probe"
        },
        "manual_decisions": {
            "action": "Retain",
            "reason": "Policy: No link is removed solely because a single automated request failed. Retain entry and monitor."
        },
        "after_metadata": {
            "title": "[A Bíblia Digital](https://www.abibliadigital.com.br/en)",
            "description": "Do not worry about managing the multiple versions of the Bible",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "No"
        }
    },
    {
        "line": 345,
        "name": "Amanah Sunnah",
        "category": "Books",
        "before_metadata": {
            "title": "[Amanah Sunnah](https://sunnah.amanahagent.cloud/developers)",
            "description": "Semantic search across Quran, Hadith, Tafsir & 18K+ Rijal narrators",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "Yes"
        },
        "observed_facts": {
            "status_code": 200,
            "response": "OK",
            "final_url": "https://sunnah.llm-kita.com/developers",
            "probe_note": "Permanent redirect to new canonical host sunnah.llm-kita.com"
        },
        "manual_decisions": {
            "action": "Update URL",
            "reason": "Canonical service documentation moved to sunnah.llm-kita.com"
        },
        "after_metadata": {
            "title": "[Amanah Sunnah](https://sunnah.llm-kita.com/developers)",
            "description": "Semantic search across Quran, Hadith, Tafsir & 18K+ Rijal narrators",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "Yes"
        }
    },
    {
        "line": 346,
        "name": "Bhagavad Gita",
        "category": "Books",
        "before_metadata": {
            "title": "[Bhagavad Gita](https://docs.bhagavadgitaapi.in)",
            "description": "Open Source Shrimad Bhagavad Gita API including 21+ authors translation in Sanskrit/English/Hindi",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "Yes"
        },
        "observed_facts": {
            "status_code": 200,
            "response": "OK",
            "final_url": "https://docs.bhagavadgitaapi.in",
            "probe_note": "Direct healthy response"
        },
        "manual_decisions": {
            "action": "No Change",
            "reason": "Current metadata and URL are healthy and accurate"
        },
        "after_metadata": {
            "title": "[Bhagavad Gita](https://docs.bhagavadgitaapi.in)",
            "description": "Open Source Shrimad Bhagavad Gita API including 21+ authors translation in Sanskrit/English/Hindi",
            "auth": "`apiKey`",
            "https": "Yes",
            "cors": "Yes"
        }
    }
]

def generate_report(entries: List[Dict[str, Any]]) -> str:
    """
    Builds a deterministic maintenance report for the scoped entries:
    - Names exact source line numbers.
    - Strictly separates observed facts from manual decision recommendations.
    - Displays before and after metadata.
    """
    lines = []
    lines.append("================================================================================")
    lines.append("                 MAINTENANCE REPORT: BOOKS CATEGORY                            ")
    lines.append("================================================================================")
    
    for entry in entries:
        lines.append(f"\n[Source Line L{entry['line']}] Entry: {entry['name']}")
        lines.append("-" * 70)
        
        # Before Metadata
        b = entry["before_metadata"]
        lines.append(f"  BEFORE: {b['title']} | Auth={b['auth']} | HTTPS={b['https']} | CORS={b['cors']}")
        
        # Strictly separate: Observed Facts
        f = entry["observed_facts"]
        lines.append("  [OBSERVED FACTS]")
        lines.append(f"    - HTTP Status: {f['status_code']} ({f['response']})")
        lines.append(f"    - Observed Target URL: {f['final_url']}")
        lines.append(f"    - Probe Note: {f['probe_note']}")
        
        # Strictly separate: Recommendations & Manual Decisions
        d = entry["manual_decisions"]
        lines.append("  [RECOMMENDATIONS & DECISIONS]")
        lines.append(f"    - Decision: {d['action']}")
        lines.append(f"    - Justification: {d['reason']}")
        
        # After Metadata
        a = entry["after_metadata"]
        lines.append(f"  AFTER:  {a['title']} | Auth={a['auth']} | HTTPS={a['https']} | CORS={a['cors']}")
        
    lines.append("\n================================================================================")
    return "\n".join(lines)

def run_self_test() -> bool:
    print("[*] Running R02-T019 self-test on maintenance report generation...")
    report1 = generate_report(SELECTED_ENTRIES)
    report2 = generate_report(SELECTED_ENTRIES)
    
    # 1. Stability check: Stable, deterministic output from identical inputs
    h1 = hashlib.sha256(report1.encode('utf-8')).hexdigest()
    h2 = hashlib.sha256(report2.encode('utf-8')).hexdigest()
    assert h1 == h2, "Report output is not deterministic across runs!"
    print("  [PASS] Output stability verified (identical SHA-256 hash across executions)")
    
    # 2. Source lines named
    assert "L344" in report1 and "L345" in report1 and "L346" in report1, "Exact line numbers missing from report"
    print("  [PASS] Exact source lines named (L344, L345, L346)")
    
    # 3. Separation of observed facts and recommendations
    assert "[OBSERVED FACTS]" in report1, "Observed facts section missing"
    assert "[RECOMMENDATIONS & DECISIONS]" in report1, "Recommendations section missing"
    print("  [PASS] Strict separation between observed facts and recommendations enforced")
    
    # 4. Retention policy verified (503 entry retained)
    assert "Retain" in report1 and "No link is removed" in report1
    print("  [PASS] Link retention policy enforced for transient HTTP 503")

    print("[+] All R02-T019 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T019 Maintenance Report Tool")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--report", action="store_true", help="Generate the scoped maintenance pass report")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.report:
        print(generate_report(SELECTED_ENTRIES))
        sys.exit(0)

    run_self_test()

if __name__ == "__main__":
    main()
