#!/usr/bin/env python3
"""Category consistency checker for assigned Public APIs entries."""

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t024"

SELECTED_APIS = {
    "mailboxlayer",
    "AGPC Domain Check",
    "Atomic Mail",
}

# Non-category introductory or promotional headings in README.md
NON_CATEGORY_HEADINGS = {
    "APIs Covered Under APILayer Suite!",
}

# Curated ground-truth registry based on verified official documentation and resources.
# Automatic classification solely by keyword matching is strictly prohibited.
VERIFIED_REGISTRY = {
    "mailboxlayer": {
        "expected_category": "Email",
        "subject": "Real-time email address validation, syntax verification, typo check, and MX-record check",
        "evidence_url": "https://mailboxlayer.com",
        "confidence": "high",
    },
    "AGPC Domain Check": {
        "expected_category": "Email",
        "subject": "Domain email deliverability and authentication records evaluation (SPF, DKIM, DMARC, MX)",
        "evidence_url": "https://guild.tradeuniquecapital.com/api",
        "confidence": "high",
    },
    "Atomic Mail": {
        "expected_category": "Email",
        "subject": "Email infrastructure for AI agents: programmatic inbox creation, sending and reading over JMAP",
        "evidence_url": "https://atomic-mail.github.io/atomic-mail-agentic/",
        "confidence": "high",
    },
    "Open Library": {
        "expected_category": "Books",
        "subject": "Book catalog, editions, authors, subject pages, and book covers",
        "evidence_url": "https://openlibrary.org/developers/api",
        "confidence": "high",
    },
    "VATlayer": {
        "expected_category": "Data Validation",
        "subject": "European VAT number validation and VAT rate lookup",
        "evidence_url": "https://vatlayer.com",
        "confidence": "high",
    },
    "US Extract": {
        "expected_category": "Data Validation",
        "subject": "Postal address extraction from freeform text; emails are only an input text source",
        "evidence_url": "https://www.smarty.com/products/apis/us-extract-api",
        "confidence": "high",
    },
}


def parse_markdown_categories(markdown_text: str) -> tuple[dict[str, list[dict]], list[dict], list[dict]]:
    """Parse categories and table rows from markdown, tracking line numbers and duplicate headings."""
    lines = markdown_text.splitlines()
    categories: dict[str, list[dict]] = {}
    all_entries: list[dict] = []
    repeated_headings: list[dict] = []
    headings_seen: dict[str, int] = {}

    current_category: str | None = None
    inside_code_block = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside_code_block = not inside_code_block
            continue

        if inside_code_block:
            continue

        # Detect category heading
        heading_match = re.match(r"^###\s+(.+?)\s*$", line)
        if heading_match:
            category_name = heading_match.group(1).strip()
            if category_name in NON_CATEGORY_HEADINGS:
                current_category = None
                continue

            if category_name in headings_seen:
                repeated_headings.append(
                    {
                        "heading": category_name,
                        "first_seen_line": headings_seen[category_name],
                        "repeated_line": line_number,
                    }
                )
            else:
                headings_seen[category_name] = line_number

            current_category = category_name
            if current_category not in categories:
                categories[current_category] = []
            continue

        if current_category is None:
            continue

        # Stop at section termination or navigation marker
        if stripped.startswith("**[⬆ Back to Index"):
            current_category = None
            continue

        # Parse API table row
        row_match = re.match(
            r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|"
            r"\s*(.*?)\s*\|\s*([^|]+?)\s*\|"
            r"\s*(Yes|No)\s*\|\s*(Yes|No|Unknown)\s*\|",
            line,
        )
        if not row_match:
            continue

        name, url, description, auth, https, cors = row_match.groups()
        auth = auth.strip().strip("`").strip()
        entry = {
            "name": name.strip(),
            "url": url.strip(),
            "description": description.strip(),
            "auth": auth,
            "https": https.strip(),
            "cors": cors.strip(),
            "category": current_category,
            "line": line_number,
        }
        categories[current_category].append(entry)
        all_entries.append(entry)

    return categories, all_entries, repeated_headings


def analyze_entry_consistency(entry: dict) -> dict:
    """Analyze whether an entry is consistent with its category without keyword guessing."""
    name = entry["name"]
    actual_category = entry["category"]

    if name in VERIFIED_REGISTRY:
        info = VERIFIED_REGISTRY[name]
        expected = info["expected_category"]
        if actual_category == expected:
            status = "consistent"
            reason = f"Verified subject ({info['subject']}) aligns with category '{actual_category}'"
            action = "none"
        else:
            status = "misplaced"
            reason = (
                f"Resource subject is '{info['subject']}', which belongs under '{expected}' "
                f"per official documentation ({info['evidence_url']})"
            )
            action = "manual_review_required"
        expected_category = expected
    else:
        status = "manual_review_required"
        expected_category = None
        reason = (
            "Insufficient official evidence to verify category placement without keyword guessing; "
            "manual review required"
        )
        action = "manual_review_required"

    return {
        "name": entry["name"],
        "url": entry["url"],
        "description": entry["description"],
        "auth": entry["auth"],
        "https": entry["https"],
        "cors": entry["cors"],
        "actual_category": actual_category,
        "expected_category": expected_category,
        "line": entry["line"],
        "status": status,
        "reason": reason,
        "proposed_action": action,
    }


def run_self_tests() -> None:
    """Run offline self-tests using fixture files and README.md."""
    # 1. Valid entry fixture
    valid_file = FIXTURES_DIR / "valid_entry.md"
    assert valid_file.exists(), f"Missing fixture: {valid_file}"
    _, entries, _ = parse_markdown_categories(valid_file.read_text(encoding="utf-8"))
    assert len(entries) == 1
    analyzed = analyze_entry_consistency(entries[0])
    assert analyzed["status"] == "consistent", f"Expected consistent, got {analyzed['status']}"
    assert analyzed["line"] == 4, f"Expected line 4, got {analyzed['line']}"
    assert analyzed["actual_category"] == "Email"

    # 2. Misplaced entry fixture
    misplaced_file = FIXTURES_DIR / "misplaced_entry.md"
    assert misplaced_file.exists(), f"Missing fixture: {misplaced_file}"
    _, entries, _ = parse_markdown_categories(misplaced_file.read_text(encoding="utf-8"))
    assert len(entries) == 1
    analyzed = analyze_entry_consistency(entries[0])
    assert analyzed["status"] == "misplaced", f"Expected misplaced, got {analyzed['status']}"
    assert analyzed["actual_category"] == "Email"
    assert analyzed["expected_category"] == "Books"
    assert analyzed["line"] == 4

    # 3. Repeated category headings fixture
    repeated_file = FIXTURES_DIR / "repeated_headings.md"
    assert repeated_file.exists(), f"Missing fixture: {repeated_file}"
    _, _, repeated = parse_markdown_categories(repeated_file.read_text(encoding="utf-8"))
    assert len(repeated) == 1, f"Expected 1 repeated heading, got {len(repeated)}"
    assert repeated[0]["heading"] == "Email"
    assert repeated[0]["first_seen_line"] == 1
    assert repeated[0]["repeated_line"] == 6, f"Expected line 6, got {repeated[0]['repeated_line']}"

    # 4. Valid category with no false positive
    valid_cat_file = FIXTURES_DIR / "valid_category_no_false_positive.md"
    assert valid_cat_file.exists(), f"Missing fixture: {valid_cat_file}"
    _, entries, _ = parse_markdown_categories(valid_cat_file.read_text(encoding="utf-8"))
    assert len(entries) == 1
    analyzed = analyze_entry_consistency(entries[0])
    assert analyzed["status"] == "consistent"
    assert analyzed["actual_category"] == "Data Validation"
    assert analyzed["line"] == 4

    # 5. Keyword distinction fixture (US Extract in Data Validation mentions 'emails')
    keyword_file = FIXTURES_DIR / "keyword_distinction.md"
    assert keyword_file.exists(), f"Missing fixture: {keyword_file}"
    _, entries, _ = parse_markdown_categories(keyword_file.read_text(encoding="utf-8"))
    assert len(entries) == 1
    analyzed = analyze_entry_consistency(entries[0])
    assert analyzed["actual_category"] == "Data Validation"
    assert analyzed["status"] == "consistent"
    # Ensure keyword 'emails' did NOT cause automatic reclassification to 'Email'
    assert analyzed["expected_category"] != "Email"
    assert analyzed["expected_category"] == "Data Validation"

    # 6. Ambiguous / missing evidence fixture
    ambiguous_file = FIXTURES_DIR / "ambiguous_entry.md"
    assert ambiguous_file.exists(), f"Missing fixture: {ambiguous_file}"
    _, entries, _ = parse_markdown_categories(ambiguous_file.read_text(encoding="utf-8"))
    assert len(entries) == 1
    analyzed = analyze_entry_consistency(entries[0])
    assert analyzed["status"] == "manual_review_required"
    assert analyzed["expected_category"] is None

    # 7. Introductory non-category heading fixture followed by a real category
    intro_file = FIXTURES_DIR / "introductory_heading.md"
    assert intro_file.exists(), f"Missing fixture: {intro_file}"
    fixture_cats, fixture_entries, fixture_repeated = parse_markdown_categories(
        intro_file.read_text(encoding="utf-8")
    )
    assert "APIs Covered Under APILayer Suite!" not in fixture_cats, (
        "Introductory heading was erroneously treated as a category in fixture"
    )
    assert "Animals" in fixture_cats, "Expected 'Animals' category in parsed fixture"
    assert len(fixture_entries) == 1, f"Expected 1 entry, got {len(fixture_entries)}"
    assert fixture_entries[0]["name"] == "Axolotl"
    assert fixture_entries[0]["category"] == "Animals"
    assert fixture_entries[0]["line"] == 11, f"Expected line 11, got {fixture_entries[0]['line']}"
    assert len(fixture_repeated) == 0, f"Expected 0 repeated headings, got {len(fixture_repeated)}"

    # 8. Real README.md parsing & verification of the 3 selected entries
    assert README.exists(), f"README.md not found at {README}"
    readme_text = README.read_text(encoding="utf-8")
    categories, all_entries, repeated_headings = parse_markdown_categories(readme_text)

    # Verify introductory heading is excluded and actual category headings parsed generically
    assert "APIs Covered Under APILayer Suite!" not in categories, (
        "Introductory heading 'APIs Covered Under APILayer Suite!' must not be treated as a category"
    )
    assert len(repeated_headings) == 0, f"Found unexpected duplicate headings in README: {repeated_headings}"
    assert "Animals" in categories, "Category 'Animals' not found in README.md"
    assert "Email" in categories, "Category 'Email' not found in README.md"
    assert len(categories) == 51, f"Expected 51 actual categories, got {len(categories)}"

    # Filter to selected entries
    selected = [e for e in all_entries if e["name"] in SELECTED_APIS]
    assert len(selected) == 3, f"Expected 3 selected entries, found {len(selected)}"

    selected_by_name = {e["name"]: e for e in selected}

    # Verify mailboxlayer
    mb = selected_by_name["mailboxlayer"]
    assert mb["category"] == "Email"
    assert mb["line"] == 983, f"Expected mailboxlayer line 983, got {mb['line']}"
    mb_eval = analyze_entry_consistency(mb)
    assert mb_eval["status"] == "consistent"

    # Verify AGPC Domain Check
    agpc = selected_by_name["AGPC Domain Check"]
    assert agpc["category"] == "Email"
    assert agpc["line"] == 984, f"Expected AGPC Domain Check line 984, got {agpc['line']}"
    agpc_eval = analyze_entry_consistency(agpc)
    assert agpc_eval["status"] == "consistent"

    # Verify Atomic Mail
    am = selected_by_name["Atomic Mail"]
    assert am["category"] == "Email"
    assert am["line"] == 985, f"Expected Atomic Mail line 985, got {am['line']}"
    am_eval = analyze_entry_consistency(am)
    assert am_eval["status"] == "consistent"

    print("All offline tests passed!")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline self-tests without external network requests",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Analyze all entries in the Email category rather than selected entries only",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    readme_text = README.read_text(encoding="utf-8")
    categories, all_entries, repeated_headings = parse_markdown_categories(readme_text)

    if args.all:
        target_entries = categories.get("Email", [])
    else:
        target_entries = [e for e in all_entries if e["name"] in SELECTED_APIS]

    # Preserve order of selected entries
    order = ["mailboxlayer", "AGPC Domain Check", "Atomic Mail"]
    if not args.all:
        target_entries.sort(key=lambda x: order.index(x["name"]) if x["name"] in order else 999)

    report = [analyze_entry_consistency(e) for e in target_entries]

    output = {
        "summary": {
            "total_evaluated": len(report),
            "consistent_count": sum(1 for r in report if r["status"] == "consistent"),
            "misplaced_count": sum(1 for r in report if r["status"] == "misplaced"),
            "manual_review_count": sum(1 for r in report if r["status"] == "manual_review_required"),
            "repeated_headings_count": len(repeated_headings),
            "repeated_headings": repeated_headings,
        },
        "entries": report,
    }

    print(json.dumps(output, indent=2))

    # Save untracked evidence to work/R02-T024/
    work_dir = ROOT / "work/R02-T024"
    work_dir.mkdir(parents=True, exist_ok=True)

    parsed_path = work_dir / "parsed-entries.json"
    parsed_path.write_text(json.dumps(target_entries, indent=2) + "\n", encoding="utf-8")

    actual_path = work_dir / "actual.json"
    actual_path.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport saved to {actual_path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
