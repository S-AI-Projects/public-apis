#!/usr/bin/env python3
"""List formatting, syntax, and ordering verification checker for assigned News APIs in public-apis."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t028"

CATEGORY = "News"
SELECTED_APIS = ["Mediastack", "Associated Press", "Chronicling America"]

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}
MAX_DESCRIPTION_LENGTH = 100

# Authoritative verified reference metadata
VERIFIED_METADATA = {
    "Mediastack": {
        "url": "https://mediastack.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers",
        "description": "Free, Simple REST API for Live News & Blog Articles",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Unknown",
        "category": "News",
    },
    "Associated Press": {
        "url": "https://developer.ap.org/",
        "description": "Search for news and metadata from Associated Press",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Unknown",
        "category": "News",
    },
    "Chronicling America": {
        "url": "http://chroniclingamerica.loc.gov/about/api/",
        "description": "Provides access to millions of pages of historic US newspapers from the Library of Congress",
        "auth": "No",
        "https": "Yes",
        "cors": "Unknown",
        "category": "News",
    },
}


# ---------------------------------------------------------------------------
# Markdown Parsing & Table Row Helpers
# ---------------------------------------------------------------------------

def split_markdown_row(line: str) -> list[str]:
    """Split a markdown table row by unescaped pipe characters '|', preserving escaped pipes '\\|'."""
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        k = len(raw) - 2
        bs = 0
        while k >= 0 and raw[k] == "\\":
            bs += 1
            k -= 1
        if bs % 2 == 0:
            raw = raw[:-1]

    cells = []
    current: list[str] = []
    i = 0
    while i < len(raw):
        ch = raw[i]
        if ch == "\\":
            if i + 1 < len(raw) and raw[i + 1] == "|":
                current.append(r"\|")
                i += 2
                continue
            current.append(ch)
            i += 1
        elif ch == "|":
            cells.append("".join(current).strip())
            current = []
            i += 1
        else:
            current.append(ch)
            i += 1

    cells.append("".join(current).strip())
    return cells


def extract_markdown_link(cell: str) -> tuple[str, str] | None:
    """
    Extract (name, url) from a Markdown link cell of format [Name](URL).
    Supports valid Markdown URLs containing balanced parentheses.
    Preserves URL text and query parameters exactly without decoding or alteration.
    """
    stripped = cell.strip()
    if not stripped.startswith("["):
        return None

    # Find the boundary ']( ' between Name and URL
    idx = -1
    for i in range(1, len(stripped) - 1):
        if stripped[i:i+2] == "](" and (i == 0 or stripped[i-1] != "\\"):
            idx = i
            break

    if idx == -1:
        return None

    name = stripped[1:idx].strip()
    if not name:
        return None

    url_part = stripped[idx + 2:]
    depth = 1
    end_idx = -1
    for i, ch in enumerate(url_part):
        if ch == "\\":
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                end_idx = i
                break

    if end_idx == -1:
        return None

    url = url_part[:end_idx].strip()
    if not url:
        return None

    return name, url


def check_heading_hierarchy(markdown_text: str, target_category: str = CATEGORY) -> tuple[bool, list[str]]:
    """
    Validate that target category heading follows the repository's H3 hierarchy ('### Category').
    Detects invalid heading levels (such as '# Category' or '## Category').
    """
    issues = []
    found_valid = False
    lines = markdown_text.splitlines()

    category_heading_re = re.compile(r"^(#{1,6})\s+" + re.escape(target_category) + r"\s*$")

    for line_num, line in enumerate(lines, start=1):
        match = category_heading_re.match(line.strip())
        if match:
            hashes = match.group(1)
            if hashes == "###":
                found_valid = True
            else:
                issues.append(
                    f"Line {line_num}: Heading '{line.strip()}' uses '{hashes}' (level {len(hashes)}); "
                    f"expected H3 ('### {target_category}')"
                )

    if not found_valid and not issues:
        issues.append(f"Missing required category heading '### {target_category}'")

    return (found_valid and len(issues) == 0), issues


def check_alphabetical_order(entries: list[dict]) -> tuple[bool, list[str], list[str]]:
    """
    Validate that entries are sorted alphabetically by title in case-insensitive order.
    Returns (is_ordered, list_of_ordering_issues, expected_sorted_order).
    Detects every adjacent ordering inversion.
    """
    issues = []
    expected_sorted_order = sorted([e["name"] for e in entries], key=lambda x: x.upper())
    if not entries:
        return True, [], []

    for i in range(len(entries) - 1):
        curr_name = entries[i]["name"]
        next_name = entries[i + 1]["name"]
        if curr_name.upper() > next_name.upper():
            issues.append(
                f"Ordering inversion: '{curr_name}' (line {entries[i]['line']}) "
                f"appears before '{next_name}' (line {entries[i + 1]['line']}); "
                f"expected '{next_name}' to precede '{curr_name}'"
            )

    return (len(issues) == 0), issues, expected_sorted_order


# ---------------------------------------------------------------------------
# News Category Parser
# ---------------------------------------------------------------------------

def parse_news_category(
    markdown_text: str,
    selected_only: bool = True,
) -> tuple[list[dict], list[dict], dict]:
    """
    Parse the News category from markdown text.
    Preserves exact original line numbers, Markdown links, query strings, and non-English text.

    Returns:
        (entries, parse_errors, metadata)
    """
    lines = markdown_text.splitlines()

    in_news = False
    entries: list[dict] = []
    all_news_entries: list[dict] = []
    parse_errors: list[dict] = []
    header_found = False
    separator_found = False
    section_start_line = None
    section_end_line = None

    heading_valid, heading_issues = check_heading_hierarchy(markdown_text, CATEGORY)

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detect category start
        if stripped == f"### {CATEGORY}":
            in_news = True
            section_start_line = line_num
            continue

        # If inside News, detect end of category
        if in_news:
            if stripped.startswith("### ") or stripped.startswith("## ") or stripped.startswith("# ") or stripped == "**[⬆ Back to Index](#index)**":
                in_news = False
                section_end_line = line_num
                break

            # Table header row
            if not header_found and ("API" in stripped and "Description" in stripped and "Auth" in stripped):
                header_found = True
                continue

            # Table delimiter row
            if not separator_found and header_found and (":---" in stripped or "---" in stripped):
                separator_found = True
                continue

            # Skip blank lines or non-table lines inside category
            if not stripped.startswith("|"):
                continue

            cells = split_markdown_row(line)

            # Validate exact column count of 5
            if len(cells) != 5:
                # Try to extract API name if possible for reporting
                maybe_link = extract_markdown_link(cells[0]) if cells else None
                name_hint = maybe_link[0] if maybe_link else (cells[0] if cells else "Unknown")
                parse_errors.append({
                    "line": line_num,
                    "api_name": name_hint,
                    "actual_columns": len(cells),
                    "expected_columns": 5,
                    "raw_line": line,
                    "message": f"Malformed table row: contains {len(cells)} columns, expected exactly 5",
                })
                continue

            # Extract title link
            title_cell = cells[0]
            link_info = extract_markdown_link(title_cell)
            if not link_info:
                parse_errors.append({
                    "line": line_num,
                    "api_name": title_cell,
                    "actual_columns": len(cells),
                    "expected_columns": 5,
                    "raw_line": line,
                    "message": f"Invalid Markdown link in Title column: '{title_cell}'",
                })
                continue

            name, url = link_info
            desc = cells[1]
            raw_auth = cells[2]
            auth = raw_auth.strip("`")
            https = cells[3]
            cors = cells[4]

            entry_data = {
                "name": name,
                "url": url,
                "description": desc,
                "auth": auth,
                "raw_auth": raw_auth,
                "https": https,
                "cors": cors,
                "category": CATEGORY,
                "line": line_num,
                "raw_line": line,
            }

            all_news_entries.append(entry_data)

            if not selected_only or name in SELECTED_APIS:
                entries.append(entry_data)

    metadata = {
        "section_start_line": section_start_line,
        "section_end_line": section_end_line,
        "header_found": header_found,
        "separator_found": separator_found,
        "heading_valid": heading_valid,
        "heading_issues": heading_issues,
        "all_news_count": len(all_news_entries),
        "all_news_entries": all_news_entries,
    }

    return entries, parse_errors, metadata


def validate_entry(entry: dict) -> dict:
    """Validate Markdown syntax, constraints, and vocabulary for a single entry."""
    issues = []
    name = entry["name"]
    desc = entry["description"]
    raw_auth = entry.get("raw_auth", entry["auth"])
    auth = entry["auth"]
    https = entry["https"]
    cors = entry["cors"]
    line_num = entry["line"]

    # 1. API Title checks
    if name.upper().endswith(" API"):
        issues.append(f"Title '{name}' ends with '... API'; should omit redundant 'API'")

    # 2. Description checks
    if not desc:
        issues.append("Missing required field: description")
    else:
        if desc[0].isupper() is False:
            issues.append(f"Description does not start with a capitalized character: '{desc}'")
        if desc[-1] in {".", ",", ";", "-"}:
            issues.append(f"Description ends with trailing punctuation '{desc[-1]}'")
        if len(desc) > MAX_DESCRIPTION_LENGTH:
            issues.append(
                f"Description length ({len(desc)}) exceeds maximum allowed {MAX_DESCRIPTION_LENGTH} characters"
            )

    # 3. Auth checks
    if not auth:
        issues.append("Missing required field: auth")
    elif auth not in VALID_AUTH:
        issues.append(f"Invalid Auth value '{auth}'; expected one of {sorted(VALID_AUTH)}")
    elif auth != "No" and not (raw_auth.startswith("`") and raw_auth.endswith("`")):
        issues.append(f"Auth value '{raw_auth}' is not enclosed in backticks")

    # 4. HTTPS checks
    if not https:
        issues.append("Missing required field: https")
    elif https not in VALID_HTTPS:
        issues.append(f"Invalid HTTPS value '{https}'; expected one of {sorted(VALID_HTTPS)}")

    # 5. CORS checks
    if not cors:
        issues.append("Missing required field: cors")
    elif cors not in VALID_CORS:
        issues.append(f"Invalid CORS value '{cors}'; expected one of {sorted(VALID_CORS)}")

    status = "valid" if not issues else "invalid"
    return {
        "status": status,
        "format_valid": (len(issues) == 0),
        "issues": issues,
    }


def check_duplicate_and_missing_entries(entries: list[dict]) -> tuple[list[str], list[str]]:
    """Detect duplicate and missing selected entries."""
    seen: dict[str, int] = {}
    duplicates: list[str] = []

    for entry in entries:
        name = entry["name"]
        if name in SELECTED_APIS:
            seen[name] = seen.get(name, 0) + 1
            if seen[name] == 2:
                duplicates.append(name)

    missing = [name for name in SELECTED_APIS if name not in seen]
    return duplicates, missing


# ---------------------------------------------------------------------------
# Offline Fixture Self-Tests
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    """Execute comprehensive offline fixture-driven verification tests."""
    print("Running self-tests for R02-T028 (Check list formatting — News)...")

    # 1. Test Valid News entries fixture
    valid_f = FIXTURES_DIR / "valid_entries.md"
    assert valid_f.exists(), f"Missing fixture: {valid_f}"
    valid_text = valid_f.read_text(encoding="utf-8")
    entries, errors, meta = parse_news_category(valid_text)
    assert len(errors) == 0, f"Expected 0 parse errors in valid fixture, got: {errors}"
    assert len(entries) == 3, f"Expected 3 entries in valid fixture, got {len(entries)}"
    assert meta["heading_valid"] is True, "Expected heading hierarchy to be valid"

    for entry in entries:
        val = validate_entry(entry)
        assert val["status"] == "valid", f"Entry {entry['name']} failed validation: {val['issues']}"

    is_ordered, order_issues, exp_order = check_alphabetical_order(entries)
    assert is_ordered is True, f"Expected valid entries to be alphabetically ordered, got {order_issues}"
    assert exp_order == ["Associated Press", "Chronicling America", "Mediastack"]

    # 2. Test Malformed Markdown/table entry fixture
    malformed_f = FIXTURES_DIR / "malformed_entry.md"
    assert malformed_f.exists(), f"Missing fixture: {malformed_f}"
    mal_text = malformed_f.read_text(encoding="utf-8")
    mal_entries, mal_errors, mal_meta = parse_news_category(mal_text)
    assert len(mal_errors) == 1, f"Expected 1 malformed parse error, got {len(mal_errors)}"
    assert mal_errors[0]["line"] == 5, f"Expected malformed row at line 5, got {mal_errors[0]['line']}"
    assert mal_errors[0]["actual_columns"] == 3, f"Expected 3 columns in malformed row, got {mal_errors[0]['actual_columns']}"
    assert mal_errors[0]["expected_columns"] == 5

    # 3. Test Missing required field fixture
    missing_f = FIXTURES_DIR / "missing_required_field.md"
    assert missing_f.exists(), f"Missing fixture: {missing_f}"
    mis_text = missing_f.read_text(encoding="utf-8")
    mis_entries, mis_errors, mis_meta = parse_news_category(mis_text)
    assert len(mis_errors) == 0, "Missing required field should parse into columns but fail field validation"
    chronicling = next(e for e in mis_entries if e["name"] == "Chronicling America")
    val_chr = validate_entry(chronicling)
    assert val_chr["status"] == "invalid", "Chronicling America should be invalid due to missing description"
    assert any("Missing required field: description" in iss for iss in val_chr["issues"]), (
        f"Expected missing description issue, got {val_chr['issues']}"
    )

    # 4. Test Incorrect ordering JSON fixture (exact 3-entry case)
    order_json_f = FIXTURES_DIR / "incorrect_ordering.json"
    assert order_json_f.exists(), f"Missing fixture: {order_json_f}"
    order_cfg = json.loads(order_json_f.read_text(encoding="utf-8"))
    ord_entries, ord_errors, ord_meta = parse_news_category(order_cfg["markdown_input"])
    assert len(ord_entries) == 3
    assert [e["name"] for e in ord_entries] == order_cfg["actual_order"]
    is_ordered, order_issues, exp_order = check_alphabetical_order(ord_entries)
    assert is_ordered is False, "Expected ordering check to detect out-of-order entries"
    assert exp_order == order_cfg["expected_sorted_order"], (
        f"Expected sorted order {order_cfg['expected_sorted_order']}, got {exp_order}"
    )
    assert len(order_issues) == len(order_cfg["expected_inversions"]), (
        f"Expected {len(order_cfg['expected_inversions'])} inversions, got {len(order_issues)}"
    )
    for exp_inv in order_cfg["expected_inversions"]:
        assert any(exp_inv["preceding"] in iss and exp_inv["following"] in iss for iss in order_issues), (
            f"Expected inversion between {exp_inv['preceding']} and {exp_inv['following']} in {order_issues}"
        )

    # Also test incorrect_ordering.md fixture
    order_md_f = FIXTURES_DIR / "incorrect_ordering.md"
    assert order_md_f.exists(), f"Missing fixture: {order_md_f}"
    ord_md_entries, _, _ = parse_news_category(order_md_f.read_text(encoding="utf-8"))
    md_is_ordered, md_order_issues, _ = check_alphabetical_order(ord_md_entries)
    assert md_is_ordered is False

    # 5. Test Invalid heading hierarchy fixture
    hierarchy_f = FIXTURES_DIR / "invalid_heading_hierarchy.md"
    assert hierarchy_f.exists(), f"Missing fixture: {hierarchy_f}"
    hier_text = hierarchy_f.read_text(encoding="utf-8")
    hier_valid, hier_issues = check_heading_hierarchy(hier_text, CATEGORY)
    assert hier_valid is False, "Expected heading hierarchy to be rejected for H2 header"
    assert any("expected H3" in iss for iss in hier_issues), f"Expected H3 error message, got: {hier_issues}"

    # 6. Test Duplicate entry fixture
    dup_f = FIXTURES_DIR / "duplicate_entry.md"
    assert dup_f.exists(), f"Missing fixture: {dup_f}"
    dup_text = dup_f.read_text(encoding="utf-8")
    dup_entries, dup_errors, dup_meta = parse_news_category(dup_text)
    dups, missing = check_duplicate_and_missing_entries(dup_entries)
    assert dups == ["Mediastack"], f"Expected duplicate entry ['Mediastack'], got {dups}"

    # 7. Test Valid non-English text fixture
    non_eng_f = FIXTURES_DIR / "valid_non_english.md"
    assert non_eng_f.exists(), f"Missing fixture: {non_eng_f}"
    non_eng_text = non_eng_f.read_text(encoding="utf-8")
    ne_entries, ne_errors, ne_meta = parse_news_category(non_eng_text)
    assert len(ne_errors) == 0
    ne_media = next(e for e in ne_entries if e["name"] == "Mediastack")
    assert "Michał Piszczek" in ne_media["description"]
    assert "São Paulo" in ne_media["description"]
    assert "München" in ne_media["description"]
    val_ne = validate_entry(ne_media)
    assert val_ne["status"] == "valid", f"Non-English valid entry failed validation: {val_ne['issues']}"

    # 8. Test Markdown links with query parameters fixture
    query_f = FIXTURES_DIR / "url_query_parameters.md"
    assert query_f.exists(), f"Missing fixture: {query_f}"
    query_text = query_f.read_text(encoding="utf-8")
    q_entries, q_errors, q_meta = parse_news_category(query_text)
    assert len(q_errors) == 0
    q_media = next(e for e in q_entries if e["name"] == "Mediastack")
    assert "utm_source=Github" in q_media["url"]
    assert "access_key=DEMO_KEY" in q_media["url"]
    assert "languages=en,es" in q_media["url"]

    # 9. Test Source line tracking fixture
    track_f = FIXTURES_DIR / "source_line_tracking.md"
    assert track_f.exists(), f"Missing fixture: {track_f}"
    track_text = track_f.read_text(encoding="utf-8")
    tr_entries, tr_errors, tr_meta = parse_news_category(track_text)
    assert len(tr_errors) == 0
    line_map = {e["name"]: e["line"] for e in tr_entries}
    assert line_map["Associated Press"] == 16, f"Expected line 16, got {line_map.get('Associated Press')}"
    assert line_map["Chronicling America"] == 17, f"Expected line 17, got {line_map.get('Chronicling America')}"
    assert line_map["Mediastack"] == 18, f"Expected line 18, got {line_map.get('Mediastack')}"

    # 10. Test Content outside assigned category fixture
    out_f = FIXTURES_DIR / "outside_category.md"
    assert out_f.exists(), f"Missing fixture: {out_f}"
    out_text = out_f.read_text(encoding="utf-8")
    out_entries, out_errors, out_meta = parse_news_category(out_text)
    assert len(out_entries) == 0, f"Entries outside News category must be ignored, got {out_entries}"

    # 11. Negative self-test check: confirm that an intentionally incorrect expectation raises an AssertionError
    deliberately_wrong_expectation = "DeliberatelyIncorrectCategory"
    assertion_raised = False
    try:
        assert entries[0]["category"] == deliberately_wrong_expectation
    except AssertionError:
        assertion_raised = True
    assert assertion_raised is True, "Negative self-test failed: assertion did not raise on deliberate mismatch!"

    print("All offline tests passed!")


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify News category formatting, syntax, and ordering in public-apis."
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=README,
        help="Path to README.md file (default: root README.md)",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Execute offline fixture-driven verification self-tests and exit",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional destination path for JSON summary report",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if not args.readme.exists():
        print(f"ERROR: Target file {args.readme} does not exist.", file=sys.stderr)
        sys.exit(1)

    markdown_text = args.readme.read_text(encoding="utf-8")

    entries, parse_errors, metadata = parse_news_category(markdown_text, selected_only=True)
    duplicates, missing = check_duplicate_and_missing_entries(entries)

    # Validate each selected entry
    reports = []
    for entry in entries:
        val = validate_entry(entry)
        reports.append({
            "name": entry["name"],
            "url": entry["url"],
            "description": entry["description"],
            "auth": entry["auth"],
            "https": entry["https"],
            "cors": entry["cors"],
            "category": entry["category"],
            "line": entry["line"],
            "format_valid": val["format_valid"],
            "status": val["status"],
            "issues": val["issues"],
        })

    # Validate ordering among the parsed entries in the News category
    # Detects every adjacent ordering inversion and includes expected sorted order
    is_ordered, ordering_issues, expected_sorted_order = check_alphabetical_order(entries)

    summary = {
        "category": CATEGORY,
        "total_selected": len(SELECTED_APIS),
        "total_parsed": len(entries),
        "duplicate_entries": duplicates,
        "missing_entries": missing,
        "heading_hierarchy_valid": metadata["heading_valid"],
        "section_boundaries_valid": (metadata["section_start_line"] is not None),
        "ordering_valid": is_ordered,
        "expected_sorted_order": expected_sorted_order,
        "ordering_issues": ordering_issues,
        "parse_errors": parse_errors,
        "valid_count": sum(1 for r in reports if r["status"] == "valid"),
        "invalid_count": sum(1 for r in reports if r["status"] == "invalid"),
        "entries": reports,
    }

    formatted_json = json.dumps(summary, indent=2, ensure_ascii=False)
    print(formatted_json)

    # Save evidence artifacts to work/R02-T028/
    work_dir = ROOT / "work/R02-T028"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = args.output or (work_dir / "actual.json")
    actual_file.write_text(formatted_json + "\n", encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nReport saved to {actual_file.relative_to(ROOT) if actual_file.is_relative_to(ROOT) else actual_file}")

    # Exit with code 1 if parsing fails, duplicates/missing entries exist, or entries are invalid
    if (
        parse_errors
        or duplicates
        or missing
        or len(entries) != len(SELECTED_APIS)
        or any(r["status"] == "invalid" for r in reports)
        or not metadata["heading_valid"]
    ):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
