#!/usr/bin/env python3
"""Repeatable maintenance pass checker for assigned Animals APIs in public-apis."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t030"

CATEGORY = "Animals"

# Fixed scope: Match strictly by URL, not display name (prevents collision with Cat Facts at line 187)
SELECTED_URLS = [
    "https://theaxolotlapi.netlify.app/",
    "https://breedhealthscore.com/developers/",
    "https://alexwohlbruck.github.io/cat-facts/",
]

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}
MAX_DESCRIPTION_LENGTH = 100

# Authoritative verified reference maintenance evidence
VERIFIED_MAINTENANCE_DATA = {
    "https://theaxolotlapi.netlify.app/": {
        "name": "Axolotl",
        "description": "Collection of axolotl pictures and facts",
        "verified_metadata": {
            "auth": "No",
            "https": "Yes",
            "cors": "No",
        },
        "inconclusive_fields": [],
        "observed_facts": {
            "documentation_url": "https://theaxolotlapi.netlify.app/",
            "http_status": 200,
            "response_classification": "successful_response",
            "https_enforced": True,
            "auth_observed": "No",
            "auth_details": "Documentation explicitly specifies 'Authentication: Axolotl does not requires an API Key'",
            "cors_observed": "No",
            "cors_details": "Documentation explicitly specifies 'Cors: Axolotl does not have CORS support for entry'",
            "endpoint_probe": {
                "endpoint_url": "https://theaxolotlapi.netlify.app/",
                "http_status": 200,
                "content_type": "text/html; charset=UTF-8",
                "endpoint_https_verified": True,
                "cors_header_present": False,
                "cors_established": True,
            },
        },
        "manual_verification_decisions": {
            "auth_decision": "No",
            "https_decision": "Yes",
            "cors_decision": "No",
            "status_decision": "operational",
            "verified_fields": ["auth", "https", "cors"],
            "inconclusive_fields": [],
            "retained_unconfirmed_fields": [],
            "decision_rationale": "Official documentation landing page is operational and explicitly documents no API key requirement, HTTPS support, and absence of CORS support. Verified values match catalogue exactly.",
        },
        "evidence_and_limitations": {
            "evidence_sources": [
                "https://theaxolotlapi.netlify.app/",
            ],
            "limitations": [
                "No dynamic interactive endpoint query parameter documentation found on landing page; metadata verified directly from provider's explicit API specification block.",
            ],
        },
    },
    "https://breedhealthscore.com/developers/": {
        "name": "Breed Health Score",
        "description": "Dog breed health scores, median lifespans and conditions",
        "verified_metadata": {
            "auth": "No",
            "https": "Yes",
            "cors": "No",
        },
        "inconclusive_fields": [],
        "observed_facts": {
            "documentation_url": "https://breedhealthscore.com/developers/",
            "http_status": 200,
            "response_classification": "successful_response",
            "https_enforced": True,
            "auth_observed": "No",
            "auth_details": "Documentation FAQ explicitly states 'No key or sign-up is required'",
            "cors_observed": "No",
            "cors_details": "API endpoint GET /api/breeds.json returns HTTP 200 without Access-Control-Allow-Origin header; OPTIONS preflight returns HTTP 405",
            "endpoint_probe": {
                "endpoint_url": "https://breedhealthscore.com/api/breeds.json",
                "http_status": 200,
                "content_type": "application/json",
                "endpoint_https_verified": True,
                "cors_header_present": False,
                "cors_established": True,
            },
        },
        "manual_verification_decisions": {
            "auth_decision": "No",
            "https_decision": "Yes",
            "cors_decision": "No",
            "status_decision": "operational",
            "verified_fields": ["auth", "https", "cors"],
            "inconclusive_fields": [],
            "retained_unconfirmed_fields": [],
            "decision_rationale": "Documentation and API endpoints are fully operational. Provider confirms open access with no key/signup. Live probe confirms HTTPS and absence of CORS headers on the API endpoint. Verified values match catalogue exactly.",
        },
        "evidence_and_limitations": {
            "evidence_sources": [
                "https://breedhealthscore.com/developers/",
                "https://breedhealthscore.com/api/breeds.json",
                "https://breedhealthscore.com/api/v1/openapi.json",
            ],
            "limitations": [
                "Static JSON dataset distributed over CDN; rate limiting is advisory ('please cache responses and be reasonable').",
            ],
        },
    },
    "https://alexwohlbruck.github.io/cat-facts/": {
        "name": "Cat Facts",
        "description": "Daily cat facts",
        "verified_metadata": {
            "auth": "No",
            "https": "Yes",
            "cors": None,
        },
        "inconclusive_fields": ["cors"],
        "observed_facts": {
            "documentation_url": "https://alexwohlbruck.github.io/cat-facts/",
            "http_status": 200,
            "response_classification": "successful_response",
            "https_enforced": True,
            "auth_observed": "No",
            "auth_details": "Documentation for /facts endpoint indicates read access without credentials; /users requires authentication",
            "cors_observed": "inconclusive",
            "cors_details": "API endpoint https://cat-fact.herokuapp.com/facts returned HTTP 503, leaving CORS unestablished. Documentation host (GitHub Pages) CORS headers do not govern the API backend.",
            "endpoint_probe": {
                "endpoint_url": "https://cat-fact.herokuapp.com/facts",
                "http_status": 503,
                "content_type": "text/html; charset=utf-8",
                "endpoint_https_verified": True,
                "cors_header_present": None,
                "cors_established": False,
            },
        },
        "manual_verification_decisions": {
            "auth_decision": "No",
            "https_decision": "Yes",
            "cors_decision": "retained_unconfirmed",
            "status_decision": "transient_http_error",
            "verified_fields": ["auth", "https"],
            "inconclusive_fields": ["cors"],
            "retained_unconfirmed_fields": ["cors"],
            "decision_rationale": "Documentation is reachable on GitHub Pages and documents unauthenticated /facts endpoints. Direct probe of API endpoint https://cat-fact.herokuapp.com/facts confirms TLS encryption/HTTPS enforcement on the API backend. Heroku backend returned HTTP 503, indicating free dyno sleeping or transient server outage, not service discontinuation. Because HTTP 503 did not establish CORS headers, CORS configuration is inconclusive; existing catalogue CORS 'No' is retained without claiming independent confirmation.",
        },
        "evidence_and_limitations": {
            "evidence_sources": [
                "https://alexwohlbruck.github.io/cat-facts/",
                "https://alexwohlbruck.github.io/cat-facts/docs",
                "https://cat-fact.herokuapp.com/facts",
            ],
            "limitations": [
                "Heroku backend returned HTTP 503; per repository policy, isolated server errors or sleeping free dynos must not be inferred as service discontinuation. CORS cannot be established on the backend during 503.",
            ],
        },
    },
}


# ---------------------------------------------------------------------------
# Classification & Helper Functions
# ---------------------------------------------------------------------------

def classify_response(
    status_code: int | None,
    is_timeout: bool = False,
    dns_error: bool = False,
    headers: dict | None = None,
) -> str:
    """
    Classify response into explicit verified categories per R02-T030 specification:
    - successful_response
    - redirect
    - authentication_required
    - blocked_or_inconclusive
    - http_error
    - timeout
    - dns_failure
    """
    if dns_error:
        return "dns_failure"
    if is_timeout:
        return "timeout"
    if status_code is None:
        return "blocked_or_inconclusive"
    if 200 <= status_code < 300:
        return "successful_response"
    if 300 <= status_code < 400:
        return "redirect"
    if status_code == 401:
        return "authentication_required"
    if status_code in (403, 429):
        return "blocked_or_inconclusive"
    if status_code >= 500:
        return "http_error"
    return "blocked_or_inconclusive"


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
    """Extract (name, url) from Markdown link format [Name](URL)."""
    stripped = cell.strip()
    if not stripped.startswith("["):
        return None

    idx = -1
    for i in range(1, len(stripped) - 1):
        if stripped[i:i + 2] == "](" and (i == 0 or stripped[i - 1] != "\\"):
            idx = i
            break

    if idx == -1:
        return None

    name = stripped[1:idx].strip()
    if not name:
        return None

    url_part = stripped[idx + 2 :]
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
    """Validate that target category heading follows H3 hierarchy ('### Category')."""
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


# ---------------------------------------------------------------------------
# Category Parser (Scoped by URL)
# ---------------------------------------------------------------------------

def parse_animals_category(
    markdown_text: str,
    selected_urls: list[str] = SELECTED_URLS,
) -> tuple[list[dict], list[dict], dict]:
    """
    Parse entries from the Animals category in markdown text.
    Matches strictly by URL rather than display name.
    Preserves exact original source line numbers.

    Returns:
        (entries, parse_errors, metadata)
    """
    lines = markdown_text.splitlines()

    in_category = False
    entries: list[dict] = []
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
            in_category = True
            section_start_line = line_num
            continue

        # If inside category, detect end of category
        if in_category:
            if (
                stripped.startswith("### ")
                or stripped.startswith("## ")
                or stripped.startswith("# ")
                or stripped == "**[⬆ Back to Index](#index)**"
            ):
                in_category = False
                section_end_line = line_num
                break

            # Table header row (handles optional trailing pipe/space)
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

            # Validate column count (5 columns: API, Description, Auth, HTTPS, CORS)
            if len(cells) != 5:
                maybe_link = extract_markdown_link(cells[0]) if cells else None
                url_hint = maybe_link[1] if maybe_link else "Unknown"
                if url_hint in selected_urls or any(u in line for u in selected_urls):
                    parse_errors.append({
                        "line": line_num,
                        "url": url_hint,
                        "actual_columns": len(cells),
                        "expected_columns": 5,
                        "raw_line": line,
                        "message": f"Malformed table row: contains {len(cells)} columns, expected exactly 5",
                    })
                continue

            title_cell = cells[0]
            link_info = extract_markdown_link(title_cell)
            if not link_info:
                parse_errors.append({
                    "line": line_num,
                    "url": "Unknown",
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
            }

            # Scope strictly to the three selected URLs (matches by URL, not name)
            if url in selected_urls:
                entries.append(entry_data)

    metadata = {
        "category": CATEGORY,
        "heading_valid": heading_valid,
        "heading_issues": heading_issues,
        "section_start_line": section_start_line,
        "section_end_line": section_end_line,
    }

    return entries, parse_errors, metadata


def check_duplicate_and_missing_urls(
    entries: list[dict],
    selected_urls: list[str] = SELECTED_URLS,
) -> tuple[list[str], list[str], list[dict]]:
    """Detect duplicate and missing entries by URL."""
    seen = set()
    duplicates = []
    cardinality_errors = []

    for entry in entries:
        url = entry["url"]
        if url in selected_urls:
            if url in seen and url not in duplicates:
                duplicates.append(url)
                cardinality_errors.append({
                    "line": entry["line"],
                    "url": url,
                    "error": f"Duplicate entry detected for URL '{url}'",
                })
            seen.add(url)

    missing = [url for url in selected_urls if url not in seen]
    for m in missing:
        cardinality_errors.append({
            "line": None,
            "url": m,
            "error": f"Missing required entry for URL '{m}'",
        })

    return duplicates, missing, cardinality_errors


# ---------------------------------------------------------------------------
# Maintenance Report Generation
# ---------------------------------------------------------------------------

def format_field_label(field: str) -> str:
    """Format field key into canonical README header string."""
    f = field.lower()
    if f == "cors":
        return "CORS"
    if f == "https":
        return "HTTPS"
    return "Auth"


def determine_recommendation(existing: dict, ref_data: dict) -> dict:
    """
    Compare existing README metadata against verified reference evidence dynamically.
    - If verified evidence contradicts the README, recommend an update and report discrepancy.
    - If existing value matches verified evidence, recommend retaining it.
    - If evidence is inconclusive (e.g. Cat Facts CORS), retain existing value without claiming
      independent confirmation.
    - Transient HTTP errors do not trigger removal or unsupported changes.
    """
    url = existing.get("url", ref_data.get("url", ""))
    name = existing.get("name", ref_data.get("name", "Unknown"))
    desc = existing.get("description", ref_data.get("description", ""))

    # Support full VERIFIED_MAINTENANCE_DATA records or simplified fixture dictionaries
    if "verified_metadata" in ref_data:
        verified_meta = ref_data["verified_metadata"]
        inconclusive_fields = set(ref_data.get("inconclusive_fields", []))
        manual_decisions = ref_data.get("manual_verification_decisions", {})
    else:
        verified_meta = {
            k: v for k, v in ref_data.items()
            if v != "inconclusive" and k in ("auth", "https", "cors")
        }
        inconclusive_fields = {
            k for k, v in ref_data.items()
            if v == "inconclusive"
        }
        manual_decisions = {"status_decision": ref_data.get("status", "operational")}

    field_actions = {}
    changes = []
    discrepancies = []
    retained_unconfirmed = []
    recommended_fields = {}

    for field in ("auth", "https", "cors"):
        existing_val = existing.get(field)
        verified_val = verified_meta.get(field)
        label = format_field_label(field)

        if field in inconclusive_fields or verified_val is None:
            # Inconclusive evidence: retain existing value without claiming confirmation
            recommended_fields[field] = existing_val
            field_actions[field] = "retain"
            retained_unconfirmed.append(field)
        elif existing_val == verified_val:
            # Matches verified evidence exactly
            recommended_fields[field] = existing_val
            field_actions[field] = "retain"
        else:
            # Contradiction: verified evidence contradicts existing catalogue
            recommended_fields[field] = verified_val
            field_actions[field] = "update"
            changes.append(f"{label}: {existing_val} -> {verified_val}")
            discrepancies.append(
                f"{label}: existing '{existing_val}' contradicts verified evidence '{verified_val}'"
            )

    has_updates = any(act == "update" for act in field_actions.values())
    overall_action = "update" if has_updates else "retain"

    # Construct human-readable reasoning
    if discrepancies:
        reasoning = (
            f"Catalogue discrepancies detected ({len(discrepancies)} field(s)). "
            f"Recommended updates: {'; '.join(changes)}."
        )
    elif retained_unconfirmed:
        reasoning = (
            f"Existing catalogue values match verified evidence for Auth and HTTPS. "
            f"Field(s) {retained_unconfirmed} retained from catalogue without claiming independent confirmation "
            f"due to inconclusive evidence ({manual_decisions.get('status_decision', 'unconfirmed')})."
        )
    else:
        reasoning = (
            f"Existing metadata matches verified evidence (Auth: {recommended_fields.get('auth')}, "
            f"HTTPS: {recommended_fields.get('https')}, CORS: {recommended_fields.get('cors')}). "
            f"No modifications required."
        )

    return {
        "name": name,
        "url": url,
        "description": desc,
        "auth": recommended_fields.get("auth"),
        "https": recommended_fields.get("https"),
        "cors": recommended_fields.get("cors"),
        "action": overall_action,
        "field_actions": field_actions,
        "changes": changes,
        "discrepancies": discrepancies,
        "retained_unconfirmed": retained_unconfirmed,
        "reasoning": reasoning,
    }


def generate_entry_maintenance_report(entry: dict) -> dict:
    """Generate structured maintenance report for a parsed entry."""
    url = entry["url"]
    ref_data = VERIFIED_MAINTENANCE_DATA.get(url)

    if not ref_data:
        return {
            "url": url,
            "name": entry.get("name", "Unknown"),
            "line": entry.get("line"),
            "existing_metadata": {
                "name": entry.get("name", ""),
                "url": url,
                "description": entry.get("description", ""),
                "auth": entry.get("auth", ""),
                "https": entry.get("https", ""),
                "cors": entry.get("cors", ""),
            },
            "observed_facts": None,
            "manual_verification_decisions": None,
            "recommended_metadata": None,
            "evidence_and_limitations": {
                "evidence_sources": [],
                "limitations": ["No reference verification record available for this URL"],
            },
        }

    recommendation = determine_recommendation(entry, ref_data)

    return {
        "url": url,
        "name": entry.get("name", "Unknown"),
        "line": entry.get("line"),
        "existing_metadata": {
            "name": entry.get("name", ""),
            "url": url,
            "description": entry.get("description", ""),
            "auth": entry.get("auth", ""),
            "https": entry.get("https", ""),
            "cors": entry.get("cors", ""),
        },
        "observed_facts": ref_data["observed_facts"],
        "manual_verification_decisions": ref_data["manual_verification_decisions"],
        "recommended_metadata": recommendation,
        "evidence_and_limitations": ref_data["evidence_and_limitations"],
    }


def generate_full_report(entries: list[dict], parse_errors: list[dict], meta: dict) -> dict:
    """Generate full deterministic maintenance report."""
    duplicates, missing, cardinality_errors = check_duplicate_and_missing_urls(entries)
    all_errors = parse_errors + cardinality_errors

    entry_reports = [generate_entry_maintenance_report(e) for e in entries]

    operational_count = 0
    transient_count = 0
    updated_count = 0
    retained_count = 0
    retained_unconfirmed_count = 0
    discrepancy_count = 0

    for rep in entry_reports:
        dec = rep.get("manual_verification_decisions") or {}
        if dec.get("status_decision") == "operational":
            operational_count += 1
        elif dec.get("status_decision") == "transient_http_error":
            transient_count += 1

        rec = rep.get("recommended_metadata") or {}
        if rec.get("action") == "retain":
            retained_count += 1
        elif rec.get("action") == "update":
            updated_count += 1

        if rec.get("retained_unconfirmed"):
            retained_unconfirmed_count += 1

        discrepancy_count += len(rec.get("discrepancies", []))

    return {
        "task": "R02-T030",
        "category": CATEGORY,
        "scope": {
            "selected_urls": SELECTED_URLS,
            "matching_strategy": "exact_url_matching",
        },
        "total_selected": len(SELECTED_URLS),
        "total_parsed": len(entries),
        "heading_hierarchy_valid": meta.get("heading_valid", True),
        "duplicate_urls": duplicates,
        "missing_urls": missing,
        "parse_errors": all_errors,
        "summary": {
            "total_evaluated": len(entry_reports),
            "retained_count": retained_count,
            "retained_unconfirmed_count": retained_unconfirmed_count,
            "updated_count": updated_count,
            "operational_count": operational_count,
            "transient_error_count": transient_count,
            "discrepancies_detected": discrepancy_count,
        },
        "entries": entry_reports,
    }


# ---------------------------------------------------------------------------
# Offline Self-Tests
# ---------------------------------------------------------------------------

def run_self_tests() -> None:
    """Run comprehensive offline test suite verifying fixtures, line tracking, URL matching, and classifications."""
    print("Running self-tests for R02-T030 (Document Repeatable Maintenance Pass — Animals)...")

    # 1. Test Valid entries fixture & URL matching (never confused with line 187 Cat Facts)
    valid_f = FIXTURES_DIR / "valid_entries.md"
    assert valid_f.exists(), f"Missing fixture: {valid_f}"
    v_entries, v_errors, v_meta = parse_animals_category(valid_f.read_text(encoding="utf-8"))
    assert len(v_errors) == 0, f"Parse errors in valid fixture: {v_errors}"
    assert len(v_entries) == 3, f"Expected exactly 3 selected entries, got {len(v_entries)}"
    assert v_meta["heading_valid"] is True

    # Assert matching is by URL, not display name
    v_urls = [e["url"] for e in v_entries]
    assert "https://theaxolotlapi.netlify.app/" in v_urls
    assert "https://breedhealthscore.com/developers/" in v_urls
    assert "https://alexwohlbruck.github.io/cat-facts/" in v_urls
    assert "https://catfact.ninja/" not in v_urls, "catfact.ninja must NOT be matched"
    print("  [PASS] 01: Valid entries parsed & URL matching verified (no display-name collision)")

    # 2. Test Source line tracking fixture
    track_f = FIXTURES_DIR / "source_line_tracking.md"
    assert track_f.exists(), f"Missing fixture: {track_f}"
    t_entries, t_errors, _ = parse_animals_category(track_f.read_text(encoding="utf-8"))
    assert len(t_errors) == 0
    t_map = {e["url"]: e["line"] for e in t_entries}
    assert t_map["https://theaxolotlapi.netlify.app/"] == 8
    assert t_map["https://breedhealthscore.com/developers/"] == 9
    assert t_map["https://alexwohlbruck.github.io/cat-facts/"] == 10
    print("  [PASS] 02: Exact source line tracking verified with preamble offsets")

    # 3. Test Duplicate URL detection fixture
    dup_f = FIXTURES_DIR / "duplicate_url.md"
    assert dup_f.exists(), f"Missing fixture: {dup_f}"
    d_entries, d_errors, _ = parse_animals_category(dup_f.read_text(encoding="utf-8"))
    assert len(d_errors) == 0
    dups, miss, card = check_duplicate_and_missing_urls(d_entries)
    assert dups == ["https://theaxolotlapi.netlify.app/"], f"Expected duplicate Axolotl URL, got {dups}"
    assert len(miss) == 0
    assert len(card) == 1
    print("  [PASS] 03: Duplicate URL correctly detected and reported")

    # 4. Test Missing required URL fixture
    miss_f = FIXTURES_DIR / "missing_entry.md"
    assert miss_f.exists(), f"Missing fixture: {miss_f}"
    m_entries, m_errors, _ = parse_animals_category(miss_f.read_text(encoding="utf-8"))
    assert len(m_errors) == 0
    dups, miss, card = check_duplicate_and_missing_urls(m_entries)
    assert len(dups) == 0
    assert miss == ["https://breedhealthscore.com/developers/"]
    assert len(card) == 1
    print("  [PASS] 04: Missing selected URL correctly flagged")

    # 5. Test Malformed table row fixture
    mal_f = FIXTURES_DIR / "malformed_row.md"
    assert mal_f.exists(), f"Missing fixture: {mal_f}"
    mal_entries, mal_errors, _ = parse_animals_category(mal_f.read_text(encoding="utf-8"))
    assert len(mal_errors) == 1
    assert mal_errors[0]["actual_columns"] == 3
    assert mal_errors[0]["expected_columns"] == 5
    assert mal_errors[0]["line"] == 4
    assert len(mal_entries) == 2
    print("  [PASS] 05: Malformed markdown row rejected with exact column counts")

    # 6. Test Outside category fixture ignored
    out_f = FIXTURES_DIR / "outside_category.md"
    assert out_f.exists(), f"Missing fixture: {out_f}"
    out_entries, out_errors, _ = parse_animals_category(out_f.read_text(encoding="utf-8"))
    assert len(out_entries) == 0, f"Entries outside {CATEGORY} must be ignored, got {out_entries}"
    print("  [PASS] 06: Target URLs outside Animals category safely ignored")

    # 7. Test URL disambiguation with multiple 'Cat Facts' entries
    dis_f = FIXTURES_DIR / "url_matching_disambiguation.md"
    assert dis_f.exists(), f"Missing fixture: {dis_f}"
    dis_entries, dis_errors, _ = parse_animals_category(dis_f.read_text(encoding="utf-8"))
    assert len(dis_errors) == 0
    assert len(dis_entries) == 3
    dis_urls = {e["url"]: e for e in dis_entries}
    assert "https://alexwohlbruck.github.io/cat-facts/" in dis_urls
    assert "https://catfact.ninja/" not in dis_urls
    assert "https://different-cat-facts.example.com/" not in dis_urls
    assert dis_urls["https://alexwohlbruck.github.io/cat-facts/"]["line"] == 4
    print("  [PASS] 07: Disambiguation of identical display names by URL confirmed")

    # 8. Test Observed facts response classification fixture
    class_f = FIXTURES_DIR / "observed_facts_classification.json"
    assert class_f.exists(), f"Missing fixture: {class_f}"
    class_data = json.loads(class_f.read_text(encoding="utf-8"))
    for tc in class_data["test_cases"]:
        inp = tc["input"]
        cls_result = classify_response(
            status_code=inp.get("status_code"),
            is_timeout=inp.get("is_timeout", False),
            dns_error=inp.get("dns_error", False),
            headers=inp.get("headers"),
        )
        assert cls_result == tc["expected_classification"], (
            f"Classification mismatch for {tc['name']}: got {cls_result}, expected {tc['expected_classification']}"
        )
    print("  [PASS] 08: Response and failure classification verified across all 7 types")

    # 9. Test Production recommendation logic covering all 4 required conditions
    rec_f = FIXTURES_DIR / "recommendations_handling.json"
    assert rec_f.exists(), f"Missing fixture: {rec_f}"
    rec_data = json.loads(rec_f.read_text(encoding="utf-8"))

    # 9.1: Verify against test fixture cases using production determine_recommendation()
    for tc in rec_data["test_cases"]:
        ex = tc["existing"]
        vf = tc["verified"]
        rec_res = determine_recommendation(ex, vf)
        assert rec_res["action"] == tc["expected_action"], (
            f"Fixture action mismatch for '{tc['description']}': "
            f"got {rec_res['action']}, expected {tc['expected_action']}"
        )
        assert rec_res["changes"] == tc["expected_changes"], (
            f"Fixture changes mismatch for '{tc['description']}': "
            f"got {rec_res['changes']}, expected {tc['expected_changes']}"
        )

    # 9.2: Condition 1: Existing metadata matching verified evidence
    match_entry = {
        "name": "Axolotl",
        "url": "https://theaxolotlapi.netlify.app/",
        "description": "Collection of axolotl pictures and facts",
        "auth": "No",
        "https": "Yes",
        "cors": "No",
    }
    match_ref = VERIFIED_MAINTENANCE_DATA["https://theaxolotlapi.netlify.app/"]
    rec_match = determine_recommendation(match_entry, match_ref)
    assert rec_match["action"] == "retain"
    assert rec_match["field_actions"] == {"auth": "retain", "https": "retain", "cors": "retain"}
    assert rec_match["changes"] == []
    assert rec_match["discrepancies"] == []
    assert rec_match["auth"] == "No"
    assert rec_match["https"] == "Yes"
    assert rec_match["cors"] == "No"

    # 9.3: Condition 2: Existing metadata contradicting verified evidence
    contradict_entry = {
        "name": "Axolotl",
        "url": "https://theaxolotlapi.netlify.app/",
        "description": "Collection of axolotl pictures and facts",
        "auth": "apiKey",
        "https": "No",
        "cors": "Yes",
    }
    rec_contra = determine_recommendation(contradict_entry, match_ref)
    assert rec_contra["action"] == "update"
    assert rec_contra["field_actions"] == {"auth": "update", "https": "update", "cors": "update"}
    assert len(rec_contra["changes"]) == 3
    assert len(rec_contra["discrepancies"]) == 3
    assert "Auth: apiKey -> No" in rec_contra["changes"]
    assert "HTTPS: No -> Yes" in rec_contra["changes"]
    assert "CORS: Yes -> No" in rec_contra["changes"]
    assert rec_contra["auth"] == "No"
    assert rec_contra["https"] == "Yes"
    assert rec_contra["cors"] == "No"

    # 9.4: Condition 3: Inconclusive evidence retaining the existing value (Cat Facts CORS)
    inconc_entry = {
        "name": "Cat Facts",
        "url": "https://alexwohlbruck.github.io/cat-facts/",
        "description": "Daily cat facts",
        "auth": "No",
        "https": "Yes",
        "cors": "No",
    }
    inconc_ref = VERIFIED_MAINTENANCE_DATA["https://alexwohlbruck.github.io/cat-facts/"]
    rec_inconc = determine_recommendation(inconc_entry, inconc_ref)
    assert rec_inconc["action"] == "retain"
    assert rec_inconc["field_actions"]["cors"] == "retain"
    assert rec_inconc["cors"] == "No"
    assert "cors" in rec_inconc["retained_unconfirmed"]
    assert rec_inconc["changes"] == []
    assert rec_inconc["discrepancies"] == []

    # 9.5: Condition 4: Transient HTTP failures not triggering removal or unsupported metadata changes
    assert inconc_ref["manual_verification_decisions"]["status_decision"] == "transient_http_error"
    transient_report = generate_entry_maintenance_report(inconc_entry)
    assert transient_report["manual_verification_decisions"]["status_decision"] == "transient_http_error"
    assert transient_report["recommended_metadata"]["action"] == "retain"
    assert transient_report["recommended_metadata"]["cors"] == "No"
    assert len(transient_report["recommended_metadata"]["changes"]) == 0
    print("  [PASS] 09: Production recommendation logic verified (matching, contradicting, inconclusive, transient 503)")

    # 10. Test Deterministic report generation & complete value comparison against fixture
    det_f = FIXTURES_DIR / "deterministic_report.json"
    assert det_f.exists(), f"Missing fixture: {det_f}"
    expected_det = json.loads(det_f.read_text(encoding="utf-8"))

    # Generate complete report using fixture input (v_entries, v_errors, v_meta from valid_entries.md)
    generated_report = generate_full_report(v_entries, v_errors, v_meta)

    # Verify summary metrics including retained_count and retained_unconfirmed_count
    assert generated_report["summary"]["retained_count"] == 3
    assert generated_report["summary"]["retained_unconfirmed_count"] == 1
    assert generated_report["summary"]["updated_count"] == 0
    assert generated_report["summary"]["discrepancies_detected"] == 0

    # Specifically verify Cat Facts is counted as retained but separately identified as unconfirmed
    cat_entry_report = next(
        e for e in generated_report["entries"]
        if e["url"] == "https://alexwohlbruck.github.io/cat-facts/"
    )
    assert cat_entry_report["recommended_metadata"]["action"] == "retain"
    assert cat_entry_report["recommended_metadata"]["retained_unconfirmed"] == ["cors"]

    # Assert complete dictionary equality
    assert generated_report == expected_det, (
        "Generated deterministic report does not match expected fixture deterministic_report.json!"
    )

    # Prove test failure if any meaningful report value changes unexpectedly
    corrupted_report = json.loads(json.dumps(generated_report))
    corrupted_report["summary"]["retained_unconfirmed_count"] = 999
    corrupted_detected = False
    try:
        assert corrupted_report == expected_det
    except AssertionError:
        corrupted_detected = True
    assert corrupted_detected is True, "Test 10 failed to detect corrupted report value!"

    print("  [PASS] 10: Complete deterministic report strictly matches expected fixture (full value comparison)")

    # 11. Negative self-test check: confirm that an intentionally incorrect assertion raises an AssertionError
    deliberately_wrong = "DeliberatelyIncorrectCategory"
    assertion_raised = False
    try:
        assert generated_report["category"] == deliberately_wrong
    except AssertionError:
        assertion_raised = True
    assert assertion_raised is True, "Negative self-test failed: assertion did not raise on deliberate mismatch!"
    print("  [PASS] 11: Intentional assertion failure correctly caught and verified")

    # 12. Test CLI --intentional-failure flag safely in an isolated subprocess
    cmd = [sys.executable, str(Path(__file__).resolve()), "--intentional-failure"]
    sub_res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert sub_res.returncode != 0, f"Expected --intentional-failure to exit non-zero, got exit code {sub_res.returncode}"
    assert (
        "ASSERTION ERROR" in sub_res.stderr
        or "intentional-failure" in sub_res.stderr
        or "intentional-failure" in sub_res.stdout
    ), f"Expected intentional failure message in output, got: {sub_res.stderr}"
    print("  [PASS] 12: CLI --intentional-failure flag safely verified to exit non-zero")

    print("\nAll offline self-tests passed successfully!")


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Repeatable maintenance pass checker for Animals APIs in public-apis."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic offline self-tests against fixtures",
    )
    parser.add_argument(
        "--intentional-failure",
        action="store_true",
        help="Deliberately fail an assertion in self-test to verify non-zero exit code",
    )
    args = parser.parse_args()

    if args.intentional_failure:
        print("Triggering intentional failure via --intentional-failure flag...", file=sys.stderr)
        assert False, "Deliberate test failure requested via --intentional-failure"

    if args.self_test:
        run_self_tests()
        return

    readme_text = README.read_text(encoding="utf-8")
    entries, parse_errors, meta = parse_animals_category(readme_text, SELECTED_URLS)

    duplicates, missing, cardinality_errors = check_duplicate_and_missing_urls(entries)
    all_errors = parse_errors + cardinality_errors

    report = generate_full_report(entries, parse_errors, meta)

    # Output formatted JSON report
    report_json = json.dumps(report, indent=2) + "\n"
    print(report_json)

    # Save evidence artifacts to work/R02-T030/
    work_dir = ROOT / "work/R02-T030"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = work_dir / "actual.json"
    actual_file.write_text(report_json, encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    print(f"\nMaintenance report saved to {actual_file.relative_to(ROOT)}")

    # Exit non-zero if there are parsing errors, duplicates, missing entries, or discrepancies
    discrepancy_count = report["summary"]["discrepancies_detected"]
    if all_errors or duplicates or missing or len(entries) != len(SELECTED_URLS) or discrepancy_count > 0:
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except AssertionError as exc:
        print(f"ASSERTION ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
    except (ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
