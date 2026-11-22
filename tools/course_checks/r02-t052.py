#!/usr/bin/env python3
"""
Course Check R02-T052: Duplicate URL Checker with Conservative Normalization.

Requirements:
- Parse README.md dynamically (never hardcode entries).
- Group EXACT duplicate URLs (byte-identical).
- Group conservative normalization matches only:
    * lowercase scheme and host
    * remove default ports (:80 for http, :443 for https)
    * remove trailing slash on path (or resolve bare host "" vs "/")
    * nothing more aggressive!
- Keep distinct:
    * query strings (including utm_* parameters)
    * meaningful fragments/anchors
    * path casing differences
    * http vs https
- Require manually reviewed pairs for any proposed deletion; reject unreviewed deletions.
- Live checks (if enabled) are sequential, timeout-bounded, max 5 hops, polite User-Agent.
- Provide comprehensive self-test with fixtures and negative testing.
"""

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple


USER_AGENT = "Mozilla/5.0 (compatible; CourseCheckerR02T052/1.0; +https://github.com/S-AI-Projects/public-apis)"


def conservative_normalize(url: str) -> Tuple[str, List[str]]:
    """
    Conservatively normalize a URL according to specification:
    1. Lowercase scheme and host.
    2. Remove default ports (:80 for http, :443 for https).
    3. Remove trailing slash on path (or bare host vs "/").
    4. Keep path casing, queries (including UTM params), and fragments intact.

    Returns:
        (normalized_url_string, list_of_normalization_reasons_applied)
    """
    raw = url.strip()
    parsed = urllib.parse.urlsplit(raw)
    reasons = []

    # 1. Scheme
    scheme_lower = parsed.scheme.lower()
    if parsed.scheme != scheme_lower:
        reasons.append("case_of_scheme")

    # 2. Host and default port
    netloc = parsed.netloc
    host_part, has_port, port_part = netloc.partition(":")

    if host_part != host_part.lower():
        reasons.append("case_of_host")

    clean_host = host_part.lower()
    final_netloc = clean_host

    if has_port:
        if (scheme_lower == "http" and port_part == "80") or (scheme_lower == "https" and port_part == "443"):
            reasons.append("default_port")
            final_netloc = clean_host
        else:
            final_netloc = f"{clean_host}:{port_part}"

    # 3. Path
    path = parsed.path
    if path == "/":
        reasons.append("trailing_slash")
        norm_path = ""
    elif path.endswith("/") and len(path) > 1:
        reasons.append("trailing_slash")
        norm_path = path.rstrip("/")
    else:
        norm_path = path

    # 4. Query and fragment are kept strictly as-is
    query = parsed.query
    fragment = parsed.fragment

    normalized = urllib.parse.urlunsplit((
        scheme_lower,
        final_netloc,
        norm_path,
        query,
        fragment
    ))
    return normalized, reasons


def get_normalization_differences(urls: List[str]) -> List[str]:
    """Find specific normalization differences between members of a duplicate group."""
    diffs = set()
    for i in range(len(urls)):
        for j in range(i + 1, len(urls)):
            u1, u2 = urls[i], urls[j]
            p1 = urllib.parse.urlsplit(u1.strip())
            p2 = urllib.parse.urlsplit(u2.strip())

            # Scheme case
            if p1.scheme != p2.scheme and p1.scheme.lower() == p2.scheme.lower():
                diffs.add("case_of_scheme")

            # Host case
            h1 = p1.netloc.partition(":")[0]
            h2 = p2.netloc.partition(":")[0]
            if h1 != h2 and h1.lower() == h2.lower():
                diffs.add("case_of_host")

            # Default port
            port1 = p1.netloc.partition(":")[2]
            port2 = p2.netloc.partition(":")[2]
            if port1 != port2:
                if (port1 in ("80", "443") and not port2) or (port2 in ("80", "443") and not port1):
                    diffs.add("default_port")

            # Trailing slash
            path1 = p1.path
            path2 = p2.path
            if path1 != path2:
                p1_norm = "" if path1 == "/" else (path1.rstrip("/") if len(path1) > 1 else path1)
                p2_norm = "" if path2 == "/" else (path2.rstrip("/") if len(path2) > 1 else path2)
                if p1_norm == p2_norm:
                    diffs.add("trailing_slash")

    return sorted(list(diffs))


def explain_distinction(url1: str, url2: str) -> str:
    """Explain why two URLs are kept distinct under conservative normalization."""
    p1 = urllib.parse.urlsplit(url1.strip())
    p2 = urllib.parse.urlsplit(url2.strip())

    if p1.scheme.lower() != p2.scheme.lower():
        return "scheme_differs_http_vs_https"

    h1 = p1.netloc.partition(":")[0].lower()
    h2 = p2.netloc.partition(":")[0].lower()
    if h1 != h2:
        return "hostname_differs"

    # Compare paths without trailing slash
    path1 = "" if p1.path == "/" else (p1.path.rstrip("/") if len(p1.path) > 1 else p1.path)
    path2 = "" if p2.path == "/" else (p2.path.rstrip("/") if len(p2.path) > 1 else p2.path)

    if path1 != path2:
        if path1.lower() == path2.lower():
            return "path_case_differs"
        return "path_differs"

    if p1.query != p2.query:
        if "utm_" in p1.query.lower() or "utm_" in p2.query.lower():
            return "query_string_differs_utm_preserved"
        return "query_string_differs"

    if p1.fragment != p2.fragment:
        return "fragment_differs"

    return "distinct_resource"


def group_entries(entries: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Group entries into exact duplicates, conservative normalized duplicates,
    or distinct entries.
    """
    # Key by normalized URL
    norm_map: Dict[str, List[Dict[str, Any]]] = {}
    for entry in entries:
        norm_url, reasons = conservative_normalize(entry["url"])
        entry_copy = dict(entry)
        entry_copy["normalized_url"] = norm_url
        entry_copy["norm_reasons"] = reasons
        norm_map.setdefault(norm_url, []).append(entry_copy)

    duplicate_groups = []
    distinct_entries = []

    for norm_url, group in norm_map.items():
        if len(group) == 1:
            distinct_entries.append(group[0])
            continue

        raw_urls = [e["url"].strip() for e in group]
        unique_raw = set(raw_urls)
        if len(unique_raw) == 1:
            match_type = "exact"
            reasons = ["byte_identical"]
        else:
            match_type = "normalized"
            diff_reasons = get_normalization_differences(raw_urls)
            reasons = diff_reasons if diff_reasons else ["conservative_normalized"]

        duplicate_groups.append({
            "match_type": match_type,
            "normalized_url": norm_url,
            "reasons": reasons,
            "lines": [e["line"] for e in group],
            "member_names": [e["name"] for e in group],
            "members": [
                {
                    "name": e["name"],
                    "url": e["url"],
                    "line": e["line"],
                    "auth": e.get("auth", ""),
                    "https": e.get("https", ""),
                    "cors": e.get("cors", "")
                }
                for e in group
            ]
        })

    # For pairwise distinct entries, explain why
    kept_distinct_reasons = []
    if len(entries) > 1 and not duplicate_groups:
        for i in range(len(entries)):
            for j in range(i + 1, len(entries)):
                e1 = entries[i]
                e2 = entries[j]
                reason = explain_distinction(e1["url"], e2["url"])
                kept_distinct_reasons.append({
                    "lines": [e1["line"], e2["line"]],
                    "reason": reason
                })

    result = {
        "duplicate_groups": duplicate_groups,
        "distinct_entries": len(distinct_entries) + (len(duplicate_groups) if duplicate_groups else 0),
        "total_input_entries": len(entries)
    }
    if kept_distinct_reasons:
        result["kept_distinct_reasons"] = kept_distinct_reasons

    return result


def validate_proposed_deletions(proposed_deletions: List[Dict[str, Any]], reviewed_pairs: List[Dict[str, Any]]) -> Tuple[bool, Optional[str]]:
    """
    Enforce manual review requirement:
    - Every proposed deletion MUST have a manually reviewed pair.
    - Missing reviewed pair or unapproved decision results in rejection.
    """
    if not proposed_deletions:
        return True, None

    if not reviewed_pairs:
        first_del = proposed_deletions[0]
        return False, f"Proposed deletion at line {first_del.get('line', '?')} rejected: missing manually reviewed pair"

    # Index reviewed pairs by removed entry line or URL
    reviewed_lines = set()
    reviewed_urls = set()
    for pair in reviewed_pairs:
        decision = pair.get("decision", "").strip().lower()
        if not decision or decision == "manual_review":
            return False, f"Pair for line {pair.get('entry_remove', {}).get('line')} requires manual review (ambiguous decision: '{decision}')"
        if decision not in ("keep_first", "keep_second", "remove_duplicate", "approved_removal"):
            return False, f"Pair for line {pair.get('entry_remove', {}).get('line')} has invalid decision: '{decision}'"

        remove_entry = pair.get("entry_remove", {})
        if "line" in remove_entry:
            reviewed_lines.add(remove_entry["line"])
        if "url" in remove_entry:
            reviewed_urls.add(remove_entry["url"].strip())

    for prop in proposed_deletions:
        line = prop.get("line")
        url = prop.get("url", "").strip()
        if line not in reviewed_lines and url not in reviewed_urls:
            return False, f"Proposed deletion at line {line} rejected: missing manually reviewed pair"

    return True, None


def parse_readme_section(readme_path: str, target_section: str = "Anti-Malware") -> List[Dict[str, Any]]:
    """Parse table entries and line numbers from a specific section in README.md."""
    if not os.path.isfile(readme_path):
        raise FileNotFoundError(f"README file not found: {readme_path}")

    with open(readme_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    section_pattern = re.compile(rf"^###\s+{re.escape(target_section)}\s*$", re.IGNORECASE)
    any_h3_pattern = re.compile(r"^###\s+")

    in_target_section = False
    entries = []

    # Table row pattern: | [Name](URL) | Description | Auth | HTTPS | CORS |
    row_pattern = re.compile(
        r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|\s*([^|]*?)\s*\|"
    )

    for idx, line in enumerate(lines, 1):
        stripped = line.strip()
        if section_pattern.match(stripped):
            in_target_section = True
            continue
        elif in_target_section and any_h3_pattern.match(stripped):
            break

        if in_target_section:
            match = row_pattern.match(stripped)
            if match:
                name, url, desc, auth, https, cors = match.groups()
                entries.append({
                    "name": name.strip(),
                    "url": url.strip(),
                    "description": desc.strip(),
                    "auth": auth.strip(),
                    "https": https.strip(),
                    "cors": cors.strip(),
                    "line": idx
                })

    return entries


def perform_live_check(entries: List[Dict[str, Any]], timeout: float = 5.0, max_hops: int = 5, request_cap: int = 5) -> List[Dict[str, Any]]:
    """
    Optional live check support evidence:
    - Sequential requests
    - Timeout on every request
    - At most 5 redirects
    - Polite User-Agent
    - Global request cap
    """
    results = []
    count = 0

    class BoundedRedirectHandler(urllib.request.HTTPRedirectHandler):
        def __init__(self, max_redirects: int):
            super().__init__()
            self.max_redirects = max_redirects
            self.redirect_count = 0

        def redirect_request(self, req, fp, code, msg, headers, newurl):
            self.redirect_count += 1
            if self.redirect_count > self.max_redirects:
                raise urllib.error.HTTPError(req.full_url, code, f"Exceeded max redirects ({self.max_redirects})", headers, fp)
            return super().redirect_request(req, fp, code, msg, headers, newurl)

    for entry in entries:
        if count >= request_cap:
            break
        count += 1
        url = entry["url"]
        record = {
            "name": entry["name"],
            "url": url,
            "line": entry["line"],
            "status": "pending"
        }
        try:
            handler = BoundedRedirectHandler(max_redirects=max_hops)
            opener = urllib.request.build_opener(handler)
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with opener.open(req, timeout=timeout) as resp:
                record["http_status"] = resp.getcode()
                record["final_url"] = resp.geturl()
                record["hops"] = handler.redirect_count
                record["status"] = "ok"
        except urllib.error.HTTPError as e:
            record["http_status"] = e.code
            record["status"] = "http_error"
            record["error"] = str(e)
        except urllib.error.URLError as e:
            record["status"] = "network_error"
            record["error"] = str(e.reason)
        except Exception as e:
            record["status"] = "exception"
            record["error"] = str(e)

        results.append(record)

    return results


def run_self_test(fixtures_dir: str) -> int:
    """Run all offline fixtures in fixtures_dir, plus negative test."""
    print("==================================================")
    print("RUNNING SELF-TEST SUITE FOR R02-T052")
    print(f"Fixtures directory: {fixtures_dir}")
    print("==================================================")

    if not os.path.isdir(fixtures_dir):
        print(f"FAIL: Fixtures directory not found: {fixtures_dir}")
        return 1

    fixture_files = sorted([f for f in os.listdir(fixtures_dir) if f.endswith(".json")])
    if not fixture_files:
        print(f"FAIL: No JSON fixture files found in {fixtures_dir}")
        return 1

    passed_count = 0
    total_count = len(fixture_files)

    for f_name in fixture_files:
        f_path = os.path.join(fixtures_dir, f_name)
        with open(f_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        test_name = data.get("test_name", f_name)
        entries = data.get("entries", [])
        expected = data.get("expected", {})
        proposed_deletions = data.get("proposed_deletions", [])
        reviewed_pairs = data.get("reviewed_pairs", [])

        print(f"\n--- Running fixture test: {test_name} ({f_name}) ---")
        print(f"Description: {data.get('description', 'N/A')}")

        try:
            # Check review validation if proposed deletions are present
            if proposed_deletions or "validation_error" in expected:
                valid, err = validate_proposed_deletions(proposed_deletions, reviewed_pairs)
                if not valid:
                    assert "validation_error" in expected, f"Unexpected validation failure: {err}"
                    assert expected["validation_error"] in err, f"Error mismatch: expected '{expected['validation_error']}', got '{err}'"
                    print(f"PASS: Correctly rejected unreviewed proposed deletion ({err})")
                    passed_count += 1
                    continue
                else:
                    assert "validation_error" not in expected, "Expected validation failure, but validation passed"

            actual = group_entries(entries)

            if "duplicate_groups" in expected:
                exp_groups = expected["duplicate_groups"]
                act_groups = actual["duplicate_groups"]
                assert len(act_groups) == len(exp_groups), (
                    f"Duplicate group count mismatch: expected {len(exp_groups)}, got {len(act_groups)}"
                )
                for exp_g, act_g in zip(exp_groups, act_groups):
                    assert act_g["match_type"] == exp_g["match_type"], (
                        f"Match type mismatch: expected {exp_g['match_type']}, got {act_g['match_type']}"
                    )
                    assert act_g["lines"] == exp_g["lines"], (
                        f"Lines mismatch: expected {exp_g['lines']}, got {act_g['lines']}"
                    )
                    for r in exp_g.get("reasons", []):
                        assert r in act_g["reasons"], (
                            f"Reason '{r}' not found in actual reasons: {act_g['reasons']}"
                        )

            if "kept_distinct_reasons" in expected:
                exp_reasons = expected["kept_distinct_reasons"]
                act_reasons = actual.get("kept_distinct_reasons", [])
                assert len(act_reasons) == len(exp_reasons), (
                    f"Kept distinct reasons count mismatch: expected {len(exp_reasons)}, got {len(act_reasons)}"
                )
                for exp_r, act_r in zip(exp_reasons, act_reasons):
                    assert act_r["reason"] == exp_r["reason"], (
                        f"Reason mismatch: expected {exp_r['reason']}, got {act_r['reason']}"
                    )

            if "distinct_entries" in expected:
                assert actual["distinct_entries"] == expected["distinct_entries"], (
                    f"Distinct entries count mismatch: expected {expected['distinct_entries']}, got {actual['distinct_entries']}"
                )

            print(f"PASS: {test_name}")
            passed_count += 1

        except AssertionError as e:
            print(f"FAIL: {test_name} - Assertion error: {e}")
            return 1
        except Exception as e:
            print(f"FAIL: {test_name} - Unexpected error: {e}")
            return 1

    print(f"\nAll {passed_count}/{total_count} fixture tests passed successfully!")

    # Negative test execution
    print("\n--------------------------------------------------")
    print("RUNNING NEGATIVE TEST (DELIBERATE FAILURE VERIFICATION)")
    print("--------------------------------------------------")
    import subprocess
    cmd = [sys.executable, os.path.abspath(__file__), "--run-negative-test-case"]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if result.returncode != 0:
        print(f"PASS: Negative test correctly exited with non-zero code ({result.returncode})")
        print(f"Negative test output preview: {result.stdout.strip()}")
    else:
        print(f"FAIL: Negative test unexpectedly exited with code 0!")
        return 1

    print("\n==================================================")
    print("SELF-TEST SUITE COMPLETED: ALL TESTS PASSED (EXIT CODE 0)")
    print("==================================================")
    return 0


def run_negative_test_case() -> int:
    """Deliberately failing test case for self-test verification."""
    print("Executing deliberately failing assertion: expecting distinct URLs to be grouped as duplicates...")
    entries = [
        {"name": "A", "url": "https://capev2.readthedocs.io/en/latest/usage/api.html?mode=1", "line": 1},
        {"name": "B", "url": "https://capev2.readthedocs.io/en/latest/usage/api.html?mode=2", "line": 2}
    ]
    res = group_entries(entries)
    # Deliberate wrong expectation: asserting duplicate_groups is not empty
    if len(res["duplicate_groups"]) == 0:
        print("Deliberate failure triggered: URLs with different query strings were correctly kept distinct, not duplicated.")
        sys.exit(3)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Course Check R02-T052: Duplicate URL Checker")
    parser.add_argument("--readme", default="README.md", help="Path to README.md")
    parser.add_argument("--section", default="Anti-Malware", help="Section name in README.md")
    parser.add_argument("--selected-only", action="store_true", help="Filter to the 3 selected entries")
    parser.add_argument("--fixtures-dir", default="tools/course_checks/fixtures/r02-t052", help="Fixtures directory")
    parser.add_argument("--self-test", action="store_true", help="Run self-test suite")
    parser.add_argument("--run-negative-test-case", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--live-check", action="store_true", help="Perform bounded live requests")
    parser.add_argument("--reviewed-pairs", help="Path to reviewed pairs JSON file")
    parser.add_argument("--proposed-deletions", help="Path to proposed deletions JSON file")
    parser.add_argument("--json", action="store_true", help="Output results in JSON format")

    args = parser.parse_args()

    if args.run_negative_test_case:
        sys.exit(run_negative_test_case())

    if args.self_test:
        sys.exit(run_self_test(args.fixtures_dir))

    # Parse README section
    entries = parse_readme_section(args.readme, args.section)
    if not entries:
        print(f"Error: No entries found in section '### {args.section}' of {args.readme}", file=sys.stderr)
        sys.exit(1)

    selected_names = {
        "AbuseIPDB",
        "AlienVault Open Threat Exchange (OTX)",
        "CAPEsandbox"
    }

    if args.selected_only:
        entries = [e for e in entries if e["name"] in selected_names]

    # Validate any proposed deletions
    proposed_deletions = []
    reviewed_pairs = []
    if args.proposed_deletions and os.path.isfile(args.proposed_deletions):
        with open(args.proposed_deletions, "r", encoding="utf-8") as f:
            proposed_deletions = json.load(f)
    if args.reviewed_pairs and os.path.isfile(args.reviewed_pairs):
        with open(args.reviewed_pairs, "r", encoding="utf-8") as f:
            reviewed_pairs = json.load(f)

    if proposed_deletions:
        valid, err = validate_proposed_deletions(proposed_deletions, reviewed_pairs)
        if not valid:
            print(f"Validation Error: {err}", file=sys.stderr)
            sys.exit(2)

    result = group_entries(entries)

    # Optional live check
    if args.live_check:
        target_live = [e for e in entries if e["name"] in selected_names]
        live_results = perform_live_check(target_live)
        result["live_check_support_evidence"] = live_results

    if args.json:
        print(json.dumps(result, indent=2))
        return

    # Readable console output
    print("==================================================")
    print(f"R02-T052 Duplicate URL Check Report")
    print(f"Section: ### {args.section}")
    print(f"Total entries analyzed: {len(entries)}")
    print("==================================================")
    print(f"Duplicate Groups Found: {len(result['duplicate_groups'])}")
    if not result["duplicate_groups"]:
        print("  -> None. All analyzed URLs are distinct under conservative normalization.")
    else:
        for idx, g in enumerate(result["duplicate_groups"], 1):
            print(f"\nGroup {idx}: [{g['match_type'].upper()}] Normalized: {g['normalized_url']}")
            print(f"  Reasons: {', '.join(g['reasons'])}")
            print("  Members:")
            for m in g["members"]:
                print(f"    - Line {m['line']}: {m['name']} -> {m['url']}")

    if "kept_distinct_reasons" in result and len(entries) <= 5:
        print("\nKept Distinct Pairwise Reasons:")
        for r in result["kept_distinct_reasons"]:
            print(f"  - Lines {r['lines']}: {r['reason']}")

    if not args.selected_only:
        print("\nAll Analyzed Section Entries (with line numbers):")
        for e in entries:
            norm_url, _ = conservative_normalize(e["url"])
            print(f"  - Line {e['line']}: {e['name']}")
            print(f"      URL:            {e['url']}")
            print(f"      Normalized URL: {norm_url}")
            print(f"      Auth:           {e['auth']}")
            print(f"      HTTPS:          {e['https']}")
            print(f"      CORS:           {e['cors']}")

    print("\nSelected Entries Summary:")
    for e in entries:
        if e["name"] in selected_names:
            norm_url, _ = conservative_normalize(e["url"])
            print(f"  - Line {e['line']}: {e['name']}")
            print(f"      URL:            {e['url']}")
            print(f"      Normalized URL: {norm_url}")
            print(f"      Auth:           {e['auth']}")
            print(f"      HTTPS:          {e['https']}")
            print(f"      CORS:           {e['cors']}")


if __name__ == "__main__":
    main()
