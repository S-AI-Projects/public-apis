#!/usr/bin/env python3
"""Conservative duplicate URL detector for the assigned Personality APIs."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t023"
CASES_FIXTURE = FIXTURES_DIR / "duplicate_cases.json"
MARKDOWN_FIXTURE = FIXTURES_DIR / "test_personality.md"

CATEGORY = "Personality"
SELECTED = {"Advice Slip", "Astro Agents", "AstroWay"}
TIMEOUT_SECONDS = 5


def normalize_url(url: str) -> str:
    """Conservatively normalize a URL for duplicate detection.

    Applied rules:
    - Lowercase scheme and hostname (RFC 3986).
    - Strip standard default ports (80 for http, 443 for https).
    - Normalize empty path to root '/' for http and https schemes.
    - Strip trailing empty fragment ('#'), preserve meaningful fragments.
    - Preserve query parameters, their values, and ordering.
    - Preserve non-root trailing slash distinctions.
    - Preserve scheme distinctions (do not merge http with https).
    """
    stripped = url.strip()
    parsed = urllib.parse.urlsplit(stripped)
    scheme = parsed.scheme.lower()

    hostname = parsed.hostname.lower() if parsed.hostname else ""
    port = parsed.port
    user = parsed.username
    password = parsed.password

    # Strip default port for scheme
    if (scheme == "http" and port == 80) or (scheme == "https" and port == 443):
        port = None

    # Reconstruct netloc
    netloc = ""
    if user:
        netloc += user
        if password:
            netloc += f":{password}"
        netloc += "@"
    if hostname:
        netloc += hostname
    if port is not None:
        netloc += f":{port}"

    # Normalize empty path to root slash for http/https
    path = parsed.path
    if not path and scheme in ("http", "https"):
        path = "/"

    query = parsed.query

    # Meaningful fragments preserved; empty fragments stripped
    fragment = parsed.fragment

    return urllib.parse.urlunsplit((scheme, netloc, path, query, fragment))


def explain_match(url1: str, url2: str) -> tuple[str, list[str]]:
    """Explain why two URLs match under conservative normalization."""
    u1 = url1.strip()
    u2 = url2.strip()
    if u1 == u2:
        return "exact", ["Exact match: URLs are identical strings."]

    reasons = []

    # Check raw scheme casing
    raw_s1 = u1.split("://", 1)[0] if "://" in u1 else ""
    raw_s2 = u2.split("://", 1)[0] if "://" in u2 else ""
    if raw_s1 != raw_s2 and raw_s1.lower() == raw_s2.lower():
        reasons.append(f"Scheme casing normalized ('{raw_s1}' vs '{raw_s2}')")

    p1 = urllib.parse.urlsplit(u1)
    p2 = urllib.parse.urlsplit(u2)

    # Check hostname casing from netloc
    host1 = (p1.netloc.split("@")[-1]).split(":")[0]
    host2 = (p2.netloc.split("@")[-1]).split(":")[0]
    if host1 != host2 and host1.lower() == host2.lower():
        reasons.append(f"Hostname casing normalized ('{host1}' vs '{host2}')")

    def is_def_port(p):
        return (p.scheme.lower() == "http" and p.port == 80) or (
            p.scheme.lower() == "https" and p.port == 443
        )

    if (is_def_port(p1) and p2.port is None) or (is_def_port(p2) and p1.port is None):
        reasons.append(f"Default port normalized ({p1.port or p2.port})")

    if (p1.path == "" and p2.path == "/") or (p1.path == "/" and p2.path == ""):
        reasons.append("Empty path normalized to root path '/'")

    if (p1.fragment == "" and p2.fragment == "") and (
        u1.endswith("#") != u2.endswith("#")
    ):
        reasons.append("Empty fragment '#' normalized away")

    if not reasons:
        reasons.append("Conservative normalization match")

    return "conservative_normalization", reasons


def parse_category_entries(
    readme_text: str, category: str = CATEGORY, selected_only: bool = False
) -> list[dict]:
    """Extract entries from the specified category table, retaining line numbers."""
    lines = readme_text.splitlines()
    in_section = False
    entries = []
    inside_code_block = False

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Handle fenced code blocks
        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside_code_block = not inside_code_block
            continue

        if inside_code_block:
            continue

        heading = re.match(r"^###\s+(.+?)\s*$", line)
        if heading:
            if in_section:
                break
            in_section = heading.group(1).strip() == category
            continue

        if not in_section:
            continue

        match = re.match(
            r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|"
            r"\s*(.*?)\s*\|\s*([^|]+?)\s*\|"
            r"\s*(Yes|No)\s*\|\s*(Yes|No|Unknown)\s*\|",
            line,
        )
        if not match:
            continue

        name, url, description, auth, https, cors = match.groups()
        auth = auth.strip().strip("`").strip()
        name_clean = name.strip()

        if selected_only and name_clean not in SELECTED:
            continue

        entries.append(
            {
                "name": name_clean,
                "url": url.strip(),
                "description": description.strip(),
                "auth": auth,
                "https": https.strip(),
                "cors": cors.strip(),
                "category": category,
                "line": line_number,
            }
        )

    if not in_section and not entries:
        raise ValueError(f"Category '{category}' not found in README text")

    return entries


def group_duplicates(entries: list[dict]) -> dict[str, list[dict]]:
    """Group entries by their conservatively normalized URL."""
    groups: dict[str, list[dict]] = {}
    for entry in entries:
        norm = normalize_url(entry["url"])
        groups.setdefault(norm, []).append(entry)
    return groups


def analyze_entry_duplicates(
    target_entries: list[dict], all_category_entries: list[dict]
) -> list[dict]:
    """Analyze duplicates for target entries against all entries in the category."""
    groups = group_duplicates(all_category_entries)
    report = []

    for entry in target_entries:
        norm = normalize_url(entry["url"])
        group = groups.get(norm, [entry])

        if len(group) == 1:
            report.append(
                {
                    **entry,
                    "normalized_url": norm,
                    "duplicate_status": "unique",
                    "duplicate_count": 0,
                    "duplicates": [],
                    "explanation": (
                        f"No duplicates detected; URL is unique within "
                        f"{entry.get('category', CATEGORY)} category"
                    ),
                }
            )
        else:
            is_canonical = entry["line"] == group[0]["line"]
            duplicates_list = []
            for other in group:
                if other["line"] == entry["line"]:
                    continue
                m_type, reasons = explain_match(entry["url"], other["url"])
                duplicates_list.append(
                    {
                        "name": other["name"],
                        "url": other["url"],
                        "line": other["line"],
                        "match_type": m_type,
                        "explanation": "; ".join(reasons),
                        "manual_review_status": "reviewed_pair",
                        "proposed_action": "manual_review_required",
                    }
                )

            report.append(
                {
                    **entry,
                    "normalized_url": norm,
                    "duplicate_status": "canonical" if is_canonical else "duplicate",
                    "duplicate_count": len(duplicates_list),
                    "duplicates": duplicates_list,
                    "explanation": (
                        f"Found {len(duplicates_list)} duplicate pair(s); "
                        f"manual review required"
                    ),
                }
            )

    return report


def check_url_live(url: str) -> dict:
    """Optional bounded live check for manual verification."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "R02-T023-Duplicate-Checker/1.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT_SECONDS) as resp:
            return {
                "live_status": resp.status,
                "live_final_url": resp.geturl(),
                "live_result": "ok" if resp.status == 200 else f"http_{resp.status}",
                "live_error": None,
            }
    except urllib.error.HTTPError as exc:
        return {
            "live_status": exc.code,
            "live_final_url": exc.geturl(),
            "live_result": f"http_{exc.code}",
            "live_error": str(exc),
        }
    except Exception as exc:
        return {
            "live_status": None,
            "live_final_url": None,
            "live_result": "request_error",
            "live_error": str(exc),
        }


def run_self_tests() -> None:
    """Run comprehensive offline self-tests using fixture files."""
    # 1. Test duplicate cases from JSON fixture
    assert CASES_FIXTURE.exists(), f"Missing fixture file: {CASES_FIXTURE}"
    cases = json.loads(CASES_FIXTURE.read_text(encoding="utf-8"))

    for case in cases:
        entries = case["entries"]
        expected_dup = case["expected_duplicate"]
        groups = group_duplicates(entries)
        has_dup = any(len(g) > 1 for g in groups.values())

        assert has_dup == expected_dup, (
            f"Case '{case['id']}': expected duplicate={expected_dup}, got {has_dup}"
        )

        if expected_dup and "expected_match_type" in case:
            m_type, reasons = explain_match(entries[0]["url"], entries[1]["url"])
            assert m_type == case["expected_match_type"], (
                f"Case '{case['id']}': expected match_type={case['expected_match_type']}, got {m_type}"
            )
            if "expected_reason_contains" in case:
                reason_str = " ".join(reasons)
                assert case["expected_reason_contains"].lower() in reason_str.lower(), (
                    f"Case '{case['id']}': expected explanation to contain "
                    f"'{case['expected_reason_contains']}', got '{reason_str}'"
                )

    # 2. Test Markdown fixture parsing and duplicate detection
    assert MARKDOWN_FIXTURE.exists(), f"Missing fixture file: {MARKDOWN_FIXTURE}"
    md_content = MARKDOWN_FIXTURE.read_text(encoding="utf-8")
    parsed_fixture = parse_category_entries(md_content, category=CATEGORY)

    # Verify code block entry was ignored
    assert all("Should be ignored" not in e["description"] for e in parsed_fixture), (
        "Code block entry was erroneously parsed"
    )

    # Verify line numbers in markdown fixture
    assert parsed_fixture[0]["name"] == "Advice Slip"
    assert parsed_fixture[0]["line"] == 9, (
        f"Expected Advice Slip line 9, got {parsed_fixture[0]['line']}"
    )

    # Verify duplicate detection in markdown fixture
    fixture_groups = group_duplicates(parsed_fixture)
    # Advice Slip (line 9) and Advice Slip Duplicate (line 15) must match
    norm_advice = normalize_url("http://api.adviceslip.com/")
    assert len(fixture_groups[norm_advice]) == 2, (
        "Expected 2 matches for Advice Slip in fixture"
    )
    # Astro Agents (line 13) and Astro Agents Upper (line 16) must match
    norm_astro = normalize_url("https://astro-agent.dev/llms.txt")
    assert len(fixture_groups[norm_astro]) == 2, (
        "Expected 2 matches for Astro Agents in fixture"
    )
    # AstroWay (line 14) and AstroWay Port (line 17) must match
    norm_astroway = normalize_url("https://api.astroway.info/docs/")
    assert len(fixture_groups[norm_astroway]) == 2, (
        "Expected 2 matches for AstroWay in fixture"
    )

    # 3. Test parsing real repository README.md Personality category
    assert README.exists(), f"README.md not found at {README}"
    readme_text = README.read_text(encoding="utf-8")
    all_personality = parse_category_entries(readme_text, category=CATEGORY)
    assert len(all_personality) >= 20, (
        f"Expected at least 20 entries in Personality, got {len(all_personality)}"
    )

    selected_entries = parse_category_entries(
        readme_text, category=CATEGORY, selected_only=True
    )
    assert len(selected_entries) == 3, (
        f"Expected 3 selected entries, got {len(selected_entries)}"
    )

    selected_names = [e["name"] for e in selected_entries]
    assert selected_names == ["Advice Slip", "Astro Agents", "AstroWay"], (
        f"Unexpected selected names: {selected_names}"
    )

    # Verify line numbers in actual README.md
    assert selected_entries[0]["line"] == 2005
    assert selected_entries[1]["line"] == 2006
    assert selected_entries[2]["line"] == 2007

    # Verify selected entries have no duplicates in actual Personality category
    report = analyze_entry_duplicates(selected_entries, all_personality)
    for item in report:
        assert item["duplicate_status"] == "unique", (
            f"Expected {item['name']} to be unique, got {item['duplicate_status']}"
        )
        assert item["duplicate_count"] == 0, (
            f"Expected 0 duplicates for {item['name']}, got {item['duplicate_count']}"
        )

    print("All offline tests passed!")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline self-tests without making network requests",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Report duplicate status for all entries in the category",
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Perform optional low-volume live verification for the selected entries",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    readme_text = README.read_text(encoding="utf-8")
    all_personality = parse_category_entries(readme_text, category=CATEGORY)

    if args.all:
        target_entries = all_personality
    else:
        target_entries = parse_category_entries(
            readme_text, category=CATEGORY, selected_only=True
        )

    report = analyze_entry_duplicates(target_entries, all_personality)

    if args.live:
        for entry in report:
            live_data = check_url_live(entry["url"])
            entry.update(live_data)
            entry["observed_at"] = date.today().isoformat()

    print(json.dumps(report, indent=2))

    # Save evidence artifacts to work/R02-T023/
    work_dir = ROOT / "work/R02-T023"
    work_dir.mkdir(parents=True, exist_ok=True)

    parsed_path = work_dir / "parsed-entries.json"
    parsed_selected = parse_category_entries(
        readme_text, category=CATEGORY, selected_only=True
    )
    parsed_path.write_text(
        json.dumps(parsed_selected, indent=2) + "\n", encoding="utf-8"
    )

    actual_path = work_dir / "actual.json"
    actual_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nReport saved to {actual_path.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
