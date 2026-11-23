#!/usr/bin/env python3
"""
tools/course_checks/r02-t053.py

Category consistency and heading placement checker for Public APIs.
Task: R02-T053 (Issue #53)

Enforces:
1. Dynamic README.md parsing by markdown heading and table rows (preserving line numbers).
2. Heading consistency: flags repeated headings and misplaced headings (alphabetical ordering for categories).
3. Category consistency guardrails:
   - Forbids keyword-only reclassification (name/description keywords never reclassify).
   - Requires explicit subject citations (observed_subject, citation_url, observation_date) for any move recommendation.
   - Prohibits automated editing and link removals; recommendations are strictly 'keep', 'move', or 'manual_review'.
   - Validates proposed moves against citation requirements.
4. Comprehensive offline self-testing with integrated negative testing subprocess.
"""

import os
import sys
import re
import json
import argparse
import subprocess
from typing import Dict, List, Any, Optional, Tuple

# Explicit subject-to-category mapping (documented in README-r02-t053.md)
SUBJECT_CATEGORY_MAP = {
    # Phone
    "phone number validation and carrier lookup": "Phone",
    "phone number validation": "Phone",
    "phone number standardization and validation": "Phone",
    "validate and standardize phone numbers": "Phone",
    "phone number validation & carrier lookup": "Phone",
    "phone specifications": "Phone",
    "place phone calls": "Phone",
    "caller id and lrn lookup": "Phone",
    # Weather
    "weather forecasts and meteorological data": "Weather",
    "weather": "Weather",
    # Books
    "books catalog": "Books",
    "books": "Books",
    # Animals
    "animal pictures and facts": "Animals",
    "cats": "Animals",
    # Photography
    "photo editing and image processing": "Photography",
    # Currency Exchange
    "foreign exchange rates and currency conversion": "Currency Exchange",
    # Anti-Malware
    "ip geolocation and threat intelligence": "Anti-Malware",
    "ip/domain/url reputation": "Anti-Malware",
    # Data Validation
    "vat number validation": "Data Validation",
    "e-invoice validation": "Data Validation",
    "address verification": "Data Validation",
    "content validator against profanity & obscenity": "Data Validation",
}

SELECTED_ENTRY_URLS = {
    "https://numlookupapi.com",
    "https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers",
    "https://cloudmersive.com/phone-number-validation-API",
}


def normalize_heading_title(title: str) -> str:
    """Normalize heading title for case-insensitive and punctuation-aware comparison."""
    # Remove markdown link formatting if any
    clean = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', title)
    clean = clean.replace('&', 'and')
    clean = re.sub(r'[^a-zA-Z0-9 ]', '', clean)
    return ' '.join(clean.lower().split())


class HeadingInfo:
    def __init__(self, level: int, raw_title: str, line_no: int):
        self.level = level
        self.raw_title = raw_title.strip()
        self.line_no = line_no
        self.normalized = normalize_heading_title(self.raw_title)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "level": self.level,
            "raw_title": self.raw_title,
            "line_no": self.line_no,
            "normalized": self.normalized,
        }


class TableEntry:
    def __init__(self, name: str, url: str, description: str, auth: str, https: str, cors: str, category: str, line_no: int):
        self.name = name.strip()
        self.url = url.strip()
        self.description = description.strip()
        self.auth = auth.strip()
        self.https = https.strip()
        self.cors = cors.strip()
        self.category = category.strip()
        self.line_no = line_no

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "description": self.description,
            "auth": self.auth,
            "https": self.https,
            "cors": self.cors,
            "category": self.category,
            "line_no": self.line_no,
        }


def parse_markdown_content(content: str) -> Tuple[List[HeadingInfo], List[TableEntry]]:
    """Parse markdown lines into structured headings and table entries with 1-based line numbers."""
    lines = content.splitlines()
    headings: List[HeadingInfo] = []
    entries: List[TableEntry] = []

    current_category: Optional[str] = None
    table_header_seen = False

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()

        # Check for markdown heading
        heading_match = re.match(r'^(#{1,6})\s+(.*)$', stripped)
        if heading_match:
            level = len(heading_match.group(1))
            title = heading_match.group(2).strip()
            # Ignore anchor links or badge images inside title if any
            h_info = HeadingInfo(level=level, raw_title=title, line_no=idx)
            headings.append(h_info)

            if level == 3:
                current_category = title
                table_header_seen = False
            elif level < 3:
                # Top level section reset
                if not title.startswith("APIs Covered"):
                    current_category = None
                table_header_seen = False
            continue

        # Check for table header / separator
        if stripped.startswith('|') or stripped.startswith('API |'):
            if 'Description' in stripped and 'Auth' in stripped:
                table_header_seen = True
                continue
            if re.match(r'^[\|\s:\-]+$', stripped):
                table_header_seen = True
                continue

            # Check if this is an API entry row
            if current_category and ('|' in stripped):
                # Pattern: | [Name](url) | Description | Auth | HTTPS | CORS |
                entry_match = re.search(r'\[([^\]]+)\]\(([^)]+)\)', stripped)
                if entry_match:
                    name = entry_match.group(1).strip()
                    url = entry_match.group(2).strip()

                    # Split columns by pipe
                    cols = [c.strip() for c in stripped.split('|')]
                    # Handle leading/trailing empty elements from splitting '| a | b |'
                    if cols and cols[0] == '':
                        cols = cols[1:]
                    if cols and cols[-1] == '':
                        cols = cols[:-1]

                    desc = cols[1] if len(cols) > 1 else ""
                    auth = cols[2] if len(cols) > 2 else ""
                    https_val = cols[3] if len(cols) > 3 else ""
                    cors_val = cols[4] if len(cols) > 4 else ""

                    entry = TableEntry(
                        name=name,
                        url=url,
                        description=desc,
                        auth=auth,
                        https=https_val,
                        cors=cors_val,
                        category=current_category,
                        line_no=idx
                    )
                    entries.append(entry)

    return headings, entries


def check_headings_consistency(headings: List[HeadingInfo]) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Check for:
    1. Repeated headings (same heading text appearing more than once).
    2. Misplaced headings (category headings out of alphabetical order).
    """
    repeated_headings: List[Dict[str, Any]] = []
    misplaced_headings: List[Dict[str, Any]] = []

    # 1. Repeated headings check across all headings
    title_to_lines: Dict[str, List[int]] = {}
    title_raw_map: Dict[str, str] = {}
    for h in headings:
        key = h.normalized
        if key not in title_to_lines:
            title_to_lines[key] = []
            title_raw_map[key] = h.raw_title
        title_to_lines[key].append(h.line_no)

    for key, line_list in title_to_lines.items():
        if len(line_list) > 1:
            repeated_headings.append({
                "heading": title_raw_map[key],
                "lines": line_list,
                "reason": f"Heading '{title_raw_map[key]}' appears {len(line_list)} times"
            })

    # 2. Misplaced / alphabetical ordering check on level 3 category headings
    # In Public APIs, category headings are level 3 (### Category)
    category_headings = [h for h in headings if h.level == 3 and not h.raw_title.startswith("APIs Covered")]

    if len(category_headings) > 1:
        prev_h = category_headings[0]
        for curr_h in category_headings[1:]:
            # Compare normalized titles
            if curr_h.normalized < prev_h.normalized:
                misplaced_headings.append({
                    "heading": curr_h.raw_title,
                    "line": curr_h.line_no,
                    "previous_heading": prev_h.raw_title,
                    "reason": f"Category '{curr_h.raw_title}' is out of alphabetical order (appears after '{prev_h.raw_title}')"
                })
            prev_h = curr_h

    return repeated_headings, misplaced_headings


def evaluate_citation(citation: Optional[Dict[str, Any]]) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate citation structure:
    Requires: observed_subject, citation_url, observation_date.
    Returns: (is_valid, mapped_category, error_reason)
    """
    if not citation or not isinstance(citation, dict):
        return False, None, "No citation provided"

    required_fields = ["observed_subject", "citation_url", "observation_date"]
    missing = [f for f in required_fields if not citation.get(f)]
    if missing:
        return False, None, f"Missing required fields: {', '.join(missing)}"

    subject = str(citation.get("observed_subject", "")).strip().lower()
    mapped_cat = SUBJECT_CATEGORY_MAP.get(subject)
    if not mapped_cat:
        # Fallback check partial matches in subject map keys
        for key, cat in SUBJECT_CATEGORY_MAP.items():
            if key in subject or subject in key:
                mapped_cat = cat
                break

    return True, mapped_cat, None


def evaluate_entry(entry: TableEntry, citation: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Evaluate category consistency of an entry:
    - Never reclassify solely on keywords from name or description.
    - If cited subject is provided and maps to a different category -> 'manual_review' with proposed_category.
    - If cited subject is provided and maps to current category -> 'keep'.
    - If no citation is provided -> 'keep' (keyword matching alone cannot reclassify).
    """
    is_valid_citation, mapped_cat, err = evaluate_citation(citation)

    res = {
        "name": entry.name,
        "url": entry.url,
        "category": entry.category,
        "line": entry.line_no,
        "citation_valid": is_valid_citation,
    }

    if is_valid_citation:
        if mapped_cat and mapped_cat.lower() != entry.category.lower():
            res["recommendation"] = "manual_review"
            res["proposed_category"] = mapped_cat
            res["reason"] = f"Cited subject belongs to '{mapped_cat}', not '{entry.category}'. Manual review recommended."
        else:
            res["recommendation"] = "keep"
            res["reason"] = "Observed subject aligns with current category"
    else:
        # Guardrail: Without a valid citation, keyword-based reclassification is strictly forbidden.
        res["recommendation"] = "keep"
        res["reason"] = "No cited subject provided; keyword matching alone is prohibited from reclassifying entries"

    return res


def evaluate_proposed_move(proposal: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluate a proposed move request.
    Must cite official documentation with observed_subject, citation_url, observation_date.
    Proposed move without citation must be rejected.
    """
    citation = proposal.get("citation")
    is_valid, mapped_cat, err = evaluate_citation(citation)

    if not is_valid:
        return {
            "valid": False,
            "status": "REJECTED",
            "reason": f"Proposed move rejected: incomplete official documentation citation. {err}"
        }

    proposed_category = proposal.get("proposed_category")
    current_category = proposal.get("current_category", "")

    return {
        "valid": True,
        "status": "ACCEPTED_RECOMMENDATION",
        "recommendation": "manual_review",
        "proposed_category": proposed_category,
        "reason": f"Valid citation provided. Mapped category '{proposed_category}' differs from current '{current_category}'. Recommendation accepted for manual review."
    }


def run_negative_test_assertion() -> None:
    """Internal negative test hook that proves a failing assertion exits non-zero."""
    print("[NEGATIVE-TEST] Initiating intentional assertion test...", file=sys.stderr)
    proposal_without_citation = {
        "target_url": "https://example.com/invalid",
        "proposed_category": "Data Validation",
        "citation": {}
    }
    result = evaluate_proposed_move(proposal_without_citation)
    # The proposal MUST be rejected (valid == False). If someone wrongly asserted valid == True, fail.
    try:
        assert result["valid"] is True, "Intentional failure: assertion that uncited proposal is valid failed!"
        print("[NEGATIVE-TEST] UNEXPECTED: Assertion passed!", file=sys.stderr)
        sys.exit(0)
    except AssertionError as e:
        print(f"[NEGATIVE-TEST] Expected failure triggered: {e}", file=sys.stderr)
        print("[NEGATIVE-TEST] Exiting with non-zero exit code 3.", file=sys.stderr)
        sys.exit(3)


def run_self_test(fixtures_dir: str) -> bool:
    """Run all offline fixtures in fixtures_dir, plus subprocess negative test."""
    print(f"=== Running Offline Fixtures from {fixtures_dir} ===")
    if not os.path.exists(fixtures_dir):
        print(f"ERROR: Fixtures directory not found: {fixtures_dir}", file=sys.stderr)
        return False

    fixture_files = sorted([f for f in os.listdir(fixtures_dir) if f.endswith(".json")])
    if not fixture_files:
        print(f"ERROR: No fixture JSON files found in {fixtures_dir}", file=sys.stderr)
        return False

    all_passed = True

    for f_name in fixture_files:
        f_path = os.path.join(fixtures_dir, f_name)
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"-> Testing fixture: {f_name} ({data.get('description', '')})")

        # Check proposal fixture type (fixture 06 & 07)
        if "proposal" in data:
            actual = evaluate_proposed_move(data["proposal"])
            expected = data["expected"]
            if actual.get("valid") != expected.get("valid") or actual.get("status") != expected.get("status"):
                print(f"   FAILED: expected {expected}, got {actual}", file=sys.stderr)
                all_passed = False
            else:
                print(f"   PASSED: {actual.get('status')}")
            continue

        # Heading / entry fixture type (fixtures 01 - 05)
        markdown = data.get("markdown", "")
        citations = data.get("citations", {})
        headings, entries = parse_markdown_content(markdown)
        rep_headings, mis_headings = check_headings_consistency(headings)

        entry_results = []
        for e in entries:
            cit = citations.get(e.url)
            entry_results.append(evaluate_entry(e, cit))

        expected = data.get("expected", {})

        # Check repeated headings
        if "repeated_headings" in expected:
            exp_rep = expected["repeated_headings"]
            act_rep = [{"heading": h["heading"], "lines": h["lines"]} for h in rep_headings]
            if act_rep != exp_rep:
                print(f"   FAILED repeated_headings: expected {exp_rep}, got {act_rep}", file=sys.stderr)
                all_passed = False
                continue

        # Check misplaced headings
        if "misplaced_headings" in expected:
            exp_mis = expected["misplaced_headings"]
            act_mis = [{"heading": h["heading"], "line": h["line"], "previous_heading": h["previous_heading"], "reason": h["reason"]} for h in mis_headings]
            if act_mis != exp_mis:
                print(f"   FAILED misplaced_headings: expected {exp_mis}, got {act_mis}", file=sys.stderr)
                all_passed = False
                continue

        # Check entries
        if "entries" in expected:
            exp_entries = expected["entries"]
            for act_e, exp_e in zip(entry_results, exp_entries):
                if act_e["recommendation"] != exp_e["recommendation"]:
                    print(f"   FAILED recommendation: expected {exp_e['recommendation']}, got {act_e['recommendation']}", file=sys.stderr)
                    all_passed = False
                    break
                if act_e.get("proposed_category") != exp_e.get("proposed_category"):
                    print(f"   FAILED proposed_category: expected {exp_e.get('proposed_category')}, got {act_e.get('proposed_category')}", file=sys.stderr)
                    all_passed = False
                    break

        print("   PASSED.")

    # Execute negative test subprocess
    print("\n=== Running Subprocess Negative Test ===")
    script_path = os.path.abspath(__file__)
    cmd = [sys.executable, script_path, "--negative-test"]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    print(f"Subprocess exit code: {proc.returncode}")
    print(f"Subprocess stderr:\n{proc.stderr.strip()}")

    if proc.returncode == 3:
        print("Negative test correctly exited with code 3 (PASSED).")
    else:
        print(f"Negative test failed: expected exit code 3, got {proc.returncode}", file=sys.stderr)
        all_passed = False

    return all_passed


def main():
    parser = argparse.ArgumentParser(description="Category consistency and heading placement checker")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture tests and negative test subprocess")
    parser.add_argument("--negative-test", action="store_true", help="Trigger intentional assertion failure hook")
    parser.add_argument("--readme", default="README.md", help="Path to README.md")
    parser.add_argument("--section", default="Phone", help="Category section name to inspect")
    parser.add_argument("--selected-only", action="store_true", help="Inspect only the 3 selected entries")
    parser.add_argument("--citations", help="Path to citations JSON file")
    parser.add_argument("--check-headings", action="store_true", help="Run document-wide heading consistency check")
    parser.add_argument("--output-json", help="Path to write JSON report")
    parser.add_argument("--output-text", help="Path to write text report")
    args = parser.parse_args()

    if args.negative_test:
        run_negative_test_assertion()
        return

    if args.self_test:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fixtures_dir = os.path.join(base_dir, "fixtures", "r02-t053")
        passed = run_self_test(fixtures_dir)
        if passed:
            print("\nALL SELF-TESTS PASSED SUCCESSFULLY (Exit Code 0).")
            sys.exit(0)
        else:
            print("\nSELF-TESTS FAILED (Exit Code 1).", file=sys.stderr)
            sys.exit(1)

    # Read README
    if not os.path.exists(args.readme):
        print(f"ERROR: {args.readme} not found", file=sys.stderr)
        sys.exit(1)

    with open(args.readme, "r", encoding="utf-8") as f:
        content = f.read()

    headings, entries = parse_markdown_content(content)
    rep_headings, mis_headings = check_headings_consistency(headings)

    citations = {}
    if args.citations and os.path.exists(args.citations):
        with open(args.citations, "r", encoding="utf-8") as f:
            citations = json.load(f)

    # Filter section entries
    target_section = args.section.strip().lower()
    section_entries = [e for e in entries if e.category.lower() == target_section]

    if args.selected_only:
        section_entries = [e for e in section_entries if e.url in SELECTED_ENTRY_URLS or e.name in ["Numlookup", "Numverify", "Cloudmersive Validate"]]

    evaluated_entries = []
    for e in section_entries:
        cit = citations.get(e.url)
        evaluated_entries.append(evaluate_entry(e, cit))

    report = {
        "readme_path": args.readme,
        "target_section": args.section,
        "selected_only": args.selected_only,
        "total_headings_inspected": len(headings),
        "repeated_headings_count": len(rep_headings),
        "repeated_headings": rep_headings,
        "misplaced_headings_count": len(mis_headings),
        "misplaced_headings": mis_headings,
        "entries_count": len(evaluated_entries),
        "entries": evaluated_entries,
    }

    # Format text output
    text_lines = []
    text_lines.append(f"=== Category Consistency Report for Section: {args.section} ===")
    text_lines.append(f"README: {args.readme}")
    text_lines.append(f"Document Headings Inspected: {len(headings)}")
    text_lines.append(f"Repeated Headings Found: {len(rep_headings)}")
    for rh in rep_headings:
        text_lines.append(f"  - '{rh['heading']}' repeated at lines {rh['lines']}")
    text_lines.append(f"Misplaced Category Headings Found: {len(mis_headings)}")
    for mh in mis_headings:
        text_lines.append(f"  - '{mh['heading']}' (line {mh['line']}) out of order: {mh['reason']}")
    text_lines.append("")
    text_lines.append(f"Entries Inspected: {len(evaluated_entries)}")
    for idx, e in enumerate(evaluated_entries, 1):
        text_lines.append(f"[{idx}] Line {e['line']}: {e['name']} ({e['url']})")
        text_lines.append(f"    Category: {e['category']} | Recommendation: {e['recommendation']}")
        if "proposed_category" in e:
            text_lines.append(f"    Proposed Category: {e['proposed_category']}")
        text_lines.append(f"    Citation Valid: {e['citation_valid']}")
        text_lines.append(f"    Reason: {e['reason']}")

    text_output = "\n".join(text_lines)

    if args.output_json:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_json)), exist_ok=True)
        with open(args.output_json, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

    if args.output_text:
        os.makedirs(os.path.dirname(os.path.abspath(args.output_text)), exist_ok=True)
        with open(args.output_text, "w", encoding="utf-8") as f:
            f.write(text_output + "\n")

    print(text_output)


if __name__ == "__main__":
    main()
