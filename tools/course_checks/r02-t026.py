#!/usr/bin/env python3
"""Metadata verification checker for assigned Development APIs in public-apis."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t026"

CATEGORY = "Development"
SELECTED_APIS = ["Userstack", "24 Pull Requests", "Aether Bridge"]

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}

# Authoritative verified metadata based on official documentation and live verification
VERIFIED_METADATA = {
    "Userstack": {
        "url": "https://userstack.com/?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers",
        "description": "Secure User-Agent String Lookup JSON API",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Unknown",
        "category": "Development",
    },
    "24 Pull Requests": {
        "url": "https://24pullrequests.com/api",
        "description": "Project to promote open source collaboration during December",
        "auth": "No",
        "https": "Yes",
        "cors": "No",
        "category": "Development",
    },
    "Aether Bridge": {
        "url": "https://a-to-mind.com",
        "description": "Autonomous agent team management and API workflow orchestration",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Unknown",
        "category": "Development",
    },
}


def split_markdown_row(line: str) -> list[str]:
    """Split a markdown table row by unescaped pipe characters '|', preserving escaped pipes '\\|'."""
    raw = line.strip()
    if raw.startswith("|"):
        raw = raw[1:]
    if raw.endswith("|"):
        # Check trailing backslashes before final pipe
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


def has_literal_pipe_in_link(line: str, name: str) -> bool:
    """Check if an unescaped literal pipe appears inside the markdown link URL for a selected API."""
    target = f"[{name}]("
    idx = line.find(target)
    if idx == -1:
        return False
    start = idx + len(target)
    depth = 1
    i = start
    while i < len(line):
        if line[i] == "\\":
            i += 2
            continue
        if line[i] == "(":
            depth += 1
        elif line[i] == ")":
            depth -= 1
            if depth == 0:
                return False
        elif line[i] == "|":
            if depth > 0:
                return True
        i += 1
    return False


def extract_markdown_link(cell: str) -> tuple[str, str] | None:
    """
    Extract (name, url) from a Markdown link cell of format [Name](URL).
    Supports valid Markdown URLs containing balanced parentheses.
    Preserves URL text exactly without decoding or altering query parameters/fragments.
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
    if not url_part.endswith(")"):
        return None

    url_content = url_part[:-1]

    # Verify parentheses inside url_content are balanced
    depth = 0
    for char in url_content:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return None
    if depth != 0:
        return None

    return name, url_content


def check_duplicate_and_missing_entries(entries: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    """
    Verify that each selected API appears exactly once.
    Returns:
      duplicate_names: list of API names appearing more than once
      missing_names: list of selected API names that do not appear
      cardinality_errors: list of error dicts describing duplicates and missing entries
    """
    counts = {name: 0 for name in SELECTED_APIS}
    for e in entries:
        name = e["name"]
        if name in counts:
            counts[name] += 1

    duplicate_names = [name for name in SELECTED_APIS if counts[name] > 1]
    missing_names = [name for name in SELECTED_APIS if counts[name] == 0]

    errors = []
    for name in duplicate_names:
        errors.append({
            "name": name,
            "category": CATEGORY,
            "error": f"Duplicate entry detected: '{name}' appears {counts[name]} times in category '{CATEGORY}' (expected exactly once)",
        })
    for name in missing_names:
        errors.append({
            "name": name,
            "category": CATEGORY,
            "error": f"Missing required entry: '{name}' was not found in category '{CATEGORY}'",
        })

    return duplicate_names, missing_names, errors


def parse_development_entries(markdown_text: str) -> tuple[list[dict], list[dict]]:
    """Parse Development category entries from markdown, preserving line numbers and capturing malformed rows."""
    lines = markdown_text.splitlines()
    in_section = False
    inside_code_block = False
    parsed_entries: list[dict] = []
    errors: list[dict] = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue

        # Section boundaries
        heading_match = re.match(r"^###\s+(.+?)\s*$", line)
        if heading_match:
            heading_title = heading_match.group(1).strip()
            if in_section:
                break
            if heading_title == CATEGORY:
                in_section = True
            continue

        if not in_section:
            continue

        if stripped.startswith("**[⬆ Back to Index"):
            break

        # Check for malformed table rows mentioning selected APIs that lack pipe delimiters
        if not stripped.startswith("|"):
            for sel_name in SELECTED_APIS:
                if sel_name in stripped:
                    errors.append({
                        "name": sel_name,
                        "line": line_number,
                        "category": CATEGORY,
                        "error": "Malformed row: table row does not start with pipe '|'",
                        "raw_line": line,
                    })
            continue

        # Skip table header and separator divider
        if stripped.startswith("|:---") or stripped.startswith("|---"):
            continue

        # Check for literal unescaped pipe inside markdown link for selected APIs
        literal_pipe_detected = False
        for sel_name in SELECTED_APIS:
            if has_literal_pipe_in_link(line, sel_name):
                errors.append({
                    "name": sel_name,
                    "line": line_number,
                    "category": CATEGORY,
                    "error": f"Literal unescaped pipe '|' detected in URL for '{sel_name}'; literal pipes cannot be safely parsed in Markdown tables and must be escaped as '\\|'",
                    "raw_line": line,
                })
                literal_pipe_detected = True
        if literal_pipe_detected:
            continue

        # Split columns by unescaped pipe
        raw_cells = split_markdown_row(line)
        if len(raw_cells) == 0:
            continue

        # Check if row is a header line e.g. "API | Description | Auth | HTTPS | CORS"
        if raw_cells[0].lower() == "api" and len(raw_cells) >= 2 and raw_cells[1].lower() == "description":
            continue

        # Extract markdown link: [Name](URL) supporting balanced parentheses
        link_info = extract_markdown_link(raw_cells[0])
        if not link_info:
            # Check if this row mentions any selected API in unformatted/malformed form
            for sel_name in SELECTED_APIS:
                if sel_name in raw_cells[0]:
                    errors.append({
                        "name": sel_name,
                        "line": line_number,
                        "category": CATEGORY,
                        "error": f"Malformed row: API name cell '{raw_cells[0]}' is not a valid markdown link [Name](URL)",
                        "raw_line": line,
                    })
            continue

        name, url = link_info

        if name not in SELECTED_APIS:
            continue

        # Check required columns: exactly 5 columns: Name(0), Description(1), Auth(2), HTTPS(3), CORS(4)
        actual_cols = len(raw_cells)
        if actual_cols != 5:
            if actual_cols < 5:
                err_msg = f"Missing required table column(s): expected exactly 5 columns, found {actual_cols}"
            else:
                err_msg = f"Extra table column(s) detected: expected exactly 5 columns, found {actual_cols}"
            errors.append({
                "name": name,
                "url": url,
                "line": line_number,
                "category": CATEGORY,
                "actual_column_count": actual_cols,
                "error": err_msg,
                "raw_line": line,
            })
            continue

        if any(raw_cells[i] == "" for i in range(5)):
            errors.append({
                "name": name,
                "url": url,
                "line": line_number,
                "category": CATEGORY,
                "actual_column_count": actual_cols,
                "error": "Empty required table column encountered in row",
                "raw_line": line,
            })
            continue

        description = raw_cells[1]
        auth = raw_cells[2].strip("`").strip()
        https = raw_cells[3]
        cors = raw_cells[4]

        parsed_entries.append({
            "name": name,
            "url": url,
            "description": description,
            "auth": auth,
            "https": https,
            "cors": cors,
            "category": CATEGORY,
            "line": line_number,
        })

    return parsed_entries, errors


def validate_entry(entry: dict) -> dict:
    """Validate entry fields against standard rules and verified reference metadata."""
    issues = []
    name = entry["name"]

    # Allowed vocabulary validation
    if entry["auth"] not in VALID_AUTH:
        issues.append(f"Invalid Auth value: '{entry['auth']}' (allowed: {sorted(VALID_AUTH)})")
    if entry["https"] not in VALID_HTTPS:
        issues.append(f"Invalid HTTPS value: '{entry['https']}' (allowed: {sorted(VALID_HTTPS)})")
    if entry["cors"] not in VALID_CORS:
        issues.append(f"Invalid CORS value: '{entry['cors']}' (allowed: {sorted(VALID_CORS)})")

    # Authoritative verification
    if name in VERIFIED_METADATA:
        expected = VERIFIED_METADATA[name]
        if entry["url"] != expected["url"]:
            issues.append(f"URL mismatch: expected '{expected['url']}', found '{entry['url']}'")
        if entry["description"] != expected["description"]:
            issues.append(f"Description mismatch: expected '{expected['description']}', found '{entry['description']}'")
        if entry["auth"] != expected["auth"]:
            issues.append(f"Auth mismatch: expected '{expected['auth']}', found '{entry['auth']}'")
        if entry["https"] != expected["https"]:
            issues.append(f"HTTPS mismatch: expected '{expected['https']}', found '{entry['https']}'")
        if entry["cors"] != expected["cors"]:
            issues.append(f"CORS mismatch: expected '{expected['cors']}', found '{entry['cors']}'")
    else:
        issues.append(f"Entry '{name}' is not in the assigned selected APIs list")

    return {
        "name": name,
        "url": entry["url"],
        "description": entry["description"],
        "auth": entry["auth"],
        "https": entry["https"],
        "cors": entry["cors"],
        "category": entry["category"],
        "line": entry["line"],
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


def run_self_tests() -> None:
    """Execute offline regression tests against fixtures and README."""
    print("Running self-tests for R02-T026 (Development Metadata Verification)...")

    # 1. Test valid entries fixture
    valid_fixture = FIXTURES_DIR / "valid_entries.md"
    assert valid_fixture.exists(), f"Missing fixture: {valid_fixture}"
    entries, errors = parse_development_entries(valid_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0, f"Unexpected parse errors: {errors}"
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"
    dups, miss, card_errs = check_duplicate_and_missing_entries(entries)
    assert len(dups) == 0 and len(miss) == 0 and len(card_errs) == 0
    for e in entries:
        val = validate_entry(e)
        assert val["status"] == "valid", f"Unexpected validation failure: {val}"

    # 2. Test missing required field fixture (< 5 columns)
    missing_fixture = FIXTURES_DIR / "missing_required_field.md"
    assert missing_fixture.exists(), f"Missing fixture: {missing_fixture}"
    entries, errors = parse_development_entries(missing_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert errors[0]["name"] == "Userstack"
    assert errors[0]["actual_column_count"] == 4
    assert "Missing required table column" in errors[0]["error"]
    assert len(entries) == 2, f"Expected 2 parsed entries, got {len(entries)}"
    assert [e["name"] for e in entries] == ["24 Pull Requests", "Aether Bridge"]

    # 3. Test extra column fixture (> 5 columns)
    extra_fixture = FIXTURES_DIR / "extra_column.md"
    assert extra_fixture.exists(), f"Missing fixture: {extra_fixture}"
    entries, errors = parse_development_entries(extra_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert errors[0]["name"] == "Userstack"
    assert errors[0]["actual_column_count"] == 6
    assert "Extra table column" in errors[0]["error"]
    assert len(entries) == 2, f"Expected 2 parsed entries, got {len(entries)}"
    assert [e["name"] for e in entries] == ["24 Pull Requests", "Aether Bridge"]

    # 4. Test malformed row fixture
    malformed_fixture = FIXTURES_DIR / "malformed_row.md"
    assert malformed_fixture.exists(), f"Missing fixture: {malformed_fixture}"
    entries, errors = parse_development_entries(malformed_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1, f"Expected 1 error, got {len(errors)}"
    assert errors[0]["name"] == "Userstack"
    assert "Malformed row" in errors[0]["error"]
    assert len(entries) == 2

    # 5. Test invalid auth fixture
    invalid_auth_fixture = FIXTURES_DIR / "invalid_auth.md"
    assert invalid_auth_fixture.exists(), f"Missing fixture: {invalid_auth_fixture}"
    entries, errors = parse_development_entries(invalid_auth_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    val_map = {e["name"]: validate_entry(e) for e in entries}
    assert any("Invalid Auth value" in issue for issue in val_map["Userstack"]["issues"])
    assert any("Invalid Auth value" in issue for issue in val_map["24 Pull Requests"]["issues"])
    assert val_map["Aether Bridge"]["status"] == "valid"

    # 6. Test invalid HTTPS and CORS fixture
    invalid_hc_fixture = FIXTURES_DIR / "invalid_https_cors.md"
    assert invalid_hc_fixture.exists(), f"Missing fixture: {invalid_hc_fixture}"
    entries, errors = parse_development_entries(invalid_hc_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    val_map = {e["name"]: validate_entry(e) for e in entries}
    assert any("Invalid HTTPS value" in issue for issue in val_map["Userstack"]["issues"])
    assert any("Invalid CORS value" in issue for issue in val_map["24 Pull Requests"]["issues"])
    assert any("Invalid HTTPS value" in issue for issue in val_map["Aether Bridge"]["issues"])

    # 7. Test incorrect metadata fixture
    incorrect_fixture = FIXTURES_DIR / "incorrect_metadata.md"
    assert incorrect_fixture.exists(), f"Missing fixture: {incorrect_fixture}"
    entries, errors = parse_development_entries(incorrect_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    val_map = {e["name"]: validate_entry(e) for e in entries}
    assert val_map["Userstack"]["status"] == "invalid"
    assert any("Auth mismatch" in issue for issue in val_map["Userstack"]["issues"])
    assert val_map["24 Pull Requests"]["status"] == "invalid"
    assert any("HTTPS mismatch" in issue for issue in val_map["24 Pull Requests"]["issues"])
    assert val_map["Aether Bridge"]["status"] == "invalid"
    assert any("CORS mismatch" in issue for issue in val_map["Aether Bridge"]["issues"])

    # 8. Test line tracking fixture
    line_fixture = FIXTURES_DIR / "line_tracking.md"
    assert line_fixture.exists(), f"Missing fixture: {line_fixture}"
    entries, errors = parse_development_entries(line_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    assert [e["line"] for e in entries] == [13, 14, 15]

    # 9. Test URL query parameters fixture
    url_qp_fixture = FIXTURES_DIR / "url_query_params.md"
    assert url_qp_fixture.exists(), f"Missing fixture: {url_qp_fixture}"
    entries, errors = parse_development_entries(url_qp_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    assert "utm_source=Github" in entries[0]["url"]
    assert "format=json&access_key=XYZ123" in entries[0]["url"]
    assert "page=2&count=99&filter=active" in entries[1]["url"]
    assert "client=web&v=2.0" in entries[2]["url"]

    # 10. Test URL fragments and special characters fixture
    url_frag_fixture = FIXTURES_DIR / "url_fragments_special_chars.md"
    assert url_frag_fixture.exists(), f"Missing fixture: {url_frag_fixture}"
    entries, errors = parse_development_entries(url_frag_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    assert "#section-quickstart_1" in entries[0]["url"]
    assert "#json-p-callbacks" in entries[1]["url"]
    assert "#agent%20management&v=1.0" in entries[2]["url"]

    # 11. Test outside development category fixture
    outside_fixture = FIXTURES_DIR / "outside_development.md"
    assert outside_fixture.exists(), f"Missing fixture: {outside_fixture}"
    entries, errors = parse_development_entries(outside_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 0, f"Expected 0 entries from outside Development, got {len(entries)}"

    # 12. Test URL with balanced parentheses
    parens_fixture = FIXTURES_DIR / "url_parentheses.md"
    assert parens_fixture.exists(), f"Missing fixture: {parens_fixture}"
    entries, errors = parse_development_entries(parens_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    assert "api(v1)/detect?query=(ua)" in entries[0]["url"]

    # 13. Test URL with escaped pipe
    escaped_pipe_fixture = FIXTURES_DIR / "escaped_pipe_url.md"
    assert escaped_pipe_fixture.exists(), f"Missing fixture: {escaped_pipe_fixture}"
    entries, errors = parse_development_entries(escaped_pipe_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3
    assert r"filter=a\|b" in entries[0]["url"]

    # 14. Test URL with literal unescaped pipe (explicitly rejected)
    literal_pipe_fixture = FIXTURES_DIR / "literal_pipe_url.md"
    assert literal_pipe_fixture.exists(), f"Missing fixture: {literal_pipe_fixture}"
    entries, errors = parse_development_entries(literal_pipe_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1
    assert errors[0]["name"] == "Userstack"
    assert "Literal unescaped pipe" in errors[0]["error"]
    assert len(entries) == 2

    # 15. Test duplicate selected API rows (even when total parsed count equals 3)
    dup_fixture = FIXTURES_DIR / "duplicate_entries.md"
    assert dup_fixture.exists(), f"Missing fixture: {dup_fixture}"
    entries, errors = parse_development_entries(dup_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3, f"Expected 3 rows parsed in duplicate fixture, got {len(entries)}"
    dups, miss, card_errs = check_duplicate_and_missing_entries(entries)
    assert dups == ["Userstack"], f"Expected duplicate Userstack, got {dups}"
    assert miss == ["Aether Bridge"], f"Expected missing Aether Bridge, got {miss}"
    assert len(card_errs) == 2
    assert any("Duplicate entry detected" in e["error"] for e in card_errs)
    assert any("Missing required entry" in e["error"] for e in card_errs)

    # 16. Test missing selected API row
    missing_entry_fixture = FIXTURES_DIR / "missing_entry.md"
    assert missing_entry_fixture.exists(), f"Missing fixture: {missing_entry_fixture}"
    entries, errors = parse_development_entries(missing_entry_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 2
    dups, miss, card_errs = check_duplicate_and_missing_entries(entries)
    assert len(dups) == 0
    assert miss == ["Aether Bridge"]
    assert len(card_errs) == 1
    assert "Missing required entry" in card_errs[0]["error"]

    # 17. Test root README.md
    assert README.exists(), f"Missing README.md at {README}"
    readme_entries, readme_errors = parse_development_entries(README.read_text(encoding="utf-8"))
    assert len(readme_errors) == 0, f"Parse errors in README.md: {readme_errors}"
    assert len(readme_entries) == 3, f"Expected 3 entries in README.md, found {len(readme_entries)}"

    readme_dups, readme_miss, readme_card_errs = check_duplicate_and_missing_entries(readme_entries)
    assert len(readme_dups) == 0, f"Duplicate entries in README: {readme_dups}"
    assert len(readme_miss) == 0, f"Missing entries in README: {readme_miss}"
    assert len(readme_card_errs) == 0

    readme_by_name = {e["name"]: e for e in readme_entries}
    assert "Userstack" in readme_by_name
    assert "24 Pull Requests" in readme_by_name
    assert "Aether Bridge" in readme_by_name

    assert readme_by_name["Userstack"]["line"] == 666
    assert readme_by_name["24 Pull Requests"]["line"] == 667
    assert readme_by_name["Aether Bridge"]["line"] == 668

    for e in readme_entries:
        v = validate_entry(e)
        assert v["status"] == "valid", f"Validation issue for {e['name']}: {v['issues']}"

    print("All offline tests passed!")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic offline self-tests against fixtures and README.md",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    readme_text = README.read_text(encoding="utf-8")
    entries, parse_errors = parse_development_entries(readme_text)

    duplicate_names, missing_names, cardinality_errors = check_duplicate_and_missing_entries(entries)
    all_errors = parse_errors + cardinality_errors

    reports = []
    for entry in entries:
        reports.append(validate_entry(entry))

    summary = {
        "category": CATEGORY,
        "total_selected": len(SELECTED_APIS),
        "total_parsed": len(entries),
        "duplicate_entries": duplicate_names,
        "missing_entries": missing_names,
        "parse_errors": all_errors,
        "valid_count": sum(1 for r in reports if r["status"] == "valid"),
        "invalid_count": sum(1 for r in reports if r["status"] == "invalid"),
        "entries": reports,
    }

    print(json.dumps(summary, indent=2))

    # Save evidence artifacts to work/R02-T026/
    work_dir = ROOT / "work/R02-T026"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = work_dir / "actual.json"
    actual_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    print(f"\nReport saved to {actual_file.relative_to(ROOT)}")

    if (
        all_errors
        or duplicate_names
        or missing_names
        or len(entries) != len(SELECTED_APIS)
        or any(r["status"] == "invalid" for r in reports)
    ):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
