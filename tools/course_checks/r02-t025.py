#!/usr/bin/env python3
"""Metadata verification checker for assigned Social APIs in public-apis."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t025"

CATEGORY = "Social"
SELECTED_APIS = ["4chan", "API Direct", "Ayrshare"]

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}

# Authoritative verified metadata based on official documentation and live verification
VERIFIED_METADATA = {
    "4chan": {
        "url": "https://github.com/4chan/4chan-API",
        "description": "Simple image-based bulletin board dedicated to a variety of topics",
        "auth": "No",
        "https": "Yes",
        "cors": "Yes",  # Supported for documented allowed origins: boards.4chan.org and boards.4channel.org
        "category": "Social",
    },
    "API Direct": {
        "url": "https://apidirect.io/docs",
        "description": "Real-time social media data from X, LinkedIn, Reddit, YouTube, Instagram, TikTok, Facebook and news",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Yes",
        "category": "Social",
    },
    "Ayrshare": {
        "url": "https://www.ayrshare.com",
        "description": "Social media APIs to post, get analytics, and manage multiple users social media accounts",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Yes",
        "category": "Social",
    },
}


def parse_social_entries(markdown_text: str) -> tuple[list[dict], list[dict]]:
    """Parse Social category entries from markdown, preserving line numbers and capturing malformed rows."""
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

        # Table header or divider
        if not stripped.startswith("|") or stripped.startswith("|:---") or stripped.startswith("|---"):
            continue

        # Split columns
        raw_cells = [c.strip() for c in stripped.strip("|").split("|")]
        if len(raw_cells) == 0:
            continue

        # Match API markdown link: [Name](URL)
        link_match = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", raw_cells[0])
        if not link_match:
            continue

        name = link_match.group(1).strip()
        url = link_match.group(2).strip()

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
    """Validate entry fields against standards and verified official metadata."""
    name = entry["name"]
    expected = VERIFIED_METADATA.get(name)

    issues = []

    # Format validations
    if not entry.get("url", "").startswith(("http://", "https://")):
        issues.append(f"Invalid URL: {entry.get('url')}")

    if len(entry.get("description", "")) > 100:
        issues.append(f"Description exceeds 100 characters ({len(entry.get('description', ''))} chars)")

    if entry.get("auth") not in VALID_AUTH:
        issues.append(f"Invalid Auth value: '{entry.get('auth')}' (must be one of {sorted(VALID_AUTH)})")

    if entry.get("https") not in VALID_HTTPS:
        issues.append(f"Invalid HTTPS value: '{entry.get('https')}' (must be one of {sorted(VALID_HTTPS)})")

    if entry.get("cors") not in VALID_CORS:
        issues.append(f"Invalid CORS value: '{entry.get('cors')}' (must be one of {sorted(VALID_CORS)})")

    # Metadata matching against verified official reference
    if expected:
        if entry.get("auth") != expected["auth"]:
            issues.append(f"Auth mismatch: observed '{entry.get('auth')}', expected '{expected['auth']}'")
        if entry.get("https") != expected["https"]:
            issues.append(f"HTTPS mismatch: observed '{entry.get('https')}', expected '{expected['https']}'")
        if entry.get("cors") != expected["cors"]:
            issues.append(f"CORS mismatch: observed '{entry.get('cors')}', expected '{expected['cors']}'")
        if entry.get("url") != expected["url"]:
            issues.append(f"URL mismatch: observed '{entry.get('url')}', expected '{expected['url']}'")

    status = "valid" if not issues else "invalid"

    return {
        **entry,
        "status": status,
        "issues": issues,
        "verified_reference": expected,
    }


def run_self_tests() -> None:
    """Run deterministic offline self-tests across fixtures and README.md."""
    # 1. Test valid entries fixture
    valid_fixture = FIXTURES_DIR / "valid_entries.md"
    assert valid_fixture.exists(), f"Missing fixture: {valid_fixture}"
    entries, errors = parse_social_entries(valid_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0, f"Expected 0 parse errors, got {errors}"
    assert len(entries) == 3, f"Expected 3 entries, got {len(entries)}"

    for entry in entries:
        validation = validate_entry(entry)
        assert validation["status"] == "valid", f"Expected valid for {entry['name']}, got {validation['issues']}"
        assert len(validation["issues"]) == 0

    assert [e["name"] for e in entries] == SELECTED_APIS
    assert [e["line"] for e in entries] == [4, 5, 6]

    # 2. Test missing required field fixture (< 5 columns)
    missing_fixture = FIXTURES_DIR / "missing_required_field.md"
    assert missing_fixture.exists(), f"Missing fixture: {missing_fixture}"
    entries, errors = parse_social_entries(missing_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1, f"Expected 1 missing field error, got {len(errors)}"
    assert errors[0]["name"] == "4chan"
    assert "Missing required table column" in errors[0]["error"]
    assert errors[0]["line"] == 4
    assert errors[0]["actual_column_count"] == 4

    # 3. Test extra column fixture (> 5 columns)
    extra_fixture = FIXTURES_DIR / "extra_column.md"
    assert extra_fixture.exists(), f"Missing fixture: {extra_fixture}"
    entries, errors = parse_social_entries(extra_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 1, f"Expected 1 extra column error, got {len(errors)}"
    assert errors[0]["name"] == "4chan"
    assert errors[0]["line"] == 4
    assert errors[0]["actual_column_count"] == 6
    assert "Extra table column" in errors[0]["error"]
    assert len(entries) == 2, f"Expected 2 parsed entries, got {len(entries)}"
    assert [e["name"] for e in entries] == ["API Direct", "Ayrshare"]

    # 4. Test incorrect metadata fixture
    incorrect_fixture = FIXTURES_DIR / "incorrect_metadata.md"
    assert incorrect_fixture.exists(), f"Missing fixture: {incorrect_fixture}"
    entries, errors = parse_social_entries(incorrect_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert len(entries) == 3

    validations = {e["name"]: validate_entry(e) for e in entries}
    assert validations["4chan"]["status"] == "invalid"
    assert any("Auth mismatch" in issue for issue in validations["4chan"]["issues"])

    assert validations["API Direct"]["status"] == "invalid"
    assert any("HTTPS mismatch" in issue for issue in validations["API Direct"]["issues"])

    assert validations["Ayrshare"]["status"] == "invalid"
    assert any("Auth mismatch" in issue for issue in validations["Ayrshare"]["issues"])

    # 4. Test invalid field values fixture
    invalid_val_fixture = FIXTURES_DIR / "invalid_field_value.md"
    assert invalid_val_fixture.exists(), f"Missing fixture: {invalid_val_fixture}"
    entries, errors = parse_social_entries(invalid_val_fixture.read_text(encoding="utf-8"))
    assert len(entries) == 3
    val_map = {e["name"]: validate_entry(e) for e in entries}
    assert any("Invalid Auth value" in issue for issue in val_map["4chan"]["issues"])
    assert any("Invalid Auth value" in issue for issue in val_map["API Direct"]["issues"])
    assert any("Invalid HTTPS value" in issue for issue in val_map["API Direct"]["issues"])
    assert any("Invalid CORS value" in issue for issue in val_map["API Direct"]["issues"])

    # 5. Test line tracking fixture
    line_fixture = FIXTURES_DIR / "line_tracking.md"
    assert line_fixture.exists(), f"Missing fixture: {line_fixture}"
    entries, errors = parse_social_entries(line_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0
    assert [e["line"] for e in entries] == [11, 12, 13]

    # 6. Test root README.md
    assert README.exists(), f"Missing README.md at {README}"
    readme_entries, readme_errors = parse_social_entries(README.read_text(encoding="utf-8"))
    assert len(readme_errors) == 0, f"Parse errors in README.md: {readme_errors}"
    assert len(readme_entries) == 3, f"Expected 3 entries in README.md, found {len(readme_entries)}"

    readme_by_name = {e["name"]: e for e in readme_entries}
    assert "4chan" in readme_by_name
    assert "API Direct" in readme_by_name
    assert "Ayrshare" in readme_by_name

    assert readme_by_name["4chan"]["line"] == 2289
    assert readme_by_name["API Direct"]["line"] == 2290
    assert readme_by_name["Ayrshare"]["line"] == 2291

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
    entries, parse_errors = parse_social_entries(readme_text)

    reports = []
    for entry in entries:
        reports.append(validate_entry(entry))

    summary = {
        "category": CATEGORY,
        "total_selected": len(SELECTED_APIS),
        "total_parsed": len(entries),
        "parse_errors": parse_errors,
        "valid_count": sum(1 for r in reports if r["status"] == "valid"),
        "invalid_count": sum(1 for r in reports if r["status"] == "invalid"),
        "entries": reports,
    }

    print(json.dumps(summary, indent=2))

    # Save evidence artifacts to work/R02-T025/
    work_dir = ROOT / "work/R02-T025"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = work_dir / "actual.json"
    actual_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    print(f"\nReport saved to {actual_file.relative_to(ROOT)}")

    if parse_errors or len(entries) != len(SELECTED_APIS) or any(r["status"] == "invalid" for r in reports):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
