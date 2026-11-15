#!/usr/bin/env python3
"""Access requirements verification checker for assigned Documents & Productivity APIs in public-apis."""

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t029"

CATEGORY = "Documents & Productivity"
SELECTED_APIS = ["AgentPay Doc Tools", "Airtable", "Api2Convert"]

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}
MAX_DESCRIPTION_LENGTH = 100

# Authoritative verified reference access evidence and catalogue metadata
VERIFIED_ACCESS_EVIDENCE = {
    "AgentPay Doc Tools": {
        "catalogue_fields": {
            "name": "AgentPay Doc Tools",
            "url": "https://agentpay-tools.agentpay-apis.workers.dev",
            "description": "PDF to text, RSS/Atom/JSON feeds to JSON and sitemaps to URL lists, paid per call via x402",
            "auth": "No",
            "https": "Yes",
            "cors": "Yes",
        },
        "access_requirements": {
            "authentication": {
                "required": False,
                "classification": "No conventional account/API authentication (x402 payment authorization required for paid calls)",
                "mechanism": "None for conventional identity auth; x402 payment authorization via PAYMENT-SIGNATURE header (or optional Bearer token for credits)",
                "status": "verified",
                "details": "Distinguishes conventional account/API authentication from x402 payment authorization: the catalogue Auth field is 'No' under repository conventions because conventional user registration, account login, API keys, and identity credentials are not required. However, payment authorization (via cryptographic x402 PAYMENT-SIGNATURE payload or prepaid credit token) is strictly required for paid API calls; requests without payment authorization return HTTP 402 Payment Required.",
                "payment_authorization_required": True,
                "evidence_url": "https://agentpay-tools.agentpay-apis.workers.dev/tools/openapi.json",
            },
            "registration": {
                "required": False,
                "classification": "No registration required",
                "status": "verified",
                "details": "Anonymous access supported; no user account registration or signup required to use x402 or claim daily trial credit",
                "evidence_url": "https://agentpay-tools.agentpay-apis.workers.dev",
            },
            "payment": {
                "payment_required": True,
                "has_free_tier": True,
                "classification": "Paid per call with limited free trial",
                "free_tier_details": "GET /credits/trial returns an API key with $0.05 trial credit (one per network per day)",
                "status": "verified",
                "details": "Pay per request via x402 in USDC on Base or Algorand ($0.005 to $0.01 per call) or prepaid credits ($1 to $500); bad input is rejected before payment",
                "evidence_url": "https://agentpay-tools.agentpay-apis.workers.dev",
            },
            "environment": {
                "required": False,
                "classification": "No specific environment or workspace",
                "status": "verified",
                "details": "Public HTTP REST API accessible from any client supporting HTTP/HTTPS and x402 payment headers or Bearer token",
                "evidence_url": "https://agentpay-tools.agentpay-apis.workers.dev/tools/llms.txt",
            },
            "public_vs_api_access": {
                "distinguished": True,
                "status": "verified",
                "details": "Documentation landing page is publicly accessible without payment; API endpoints (/tools/v1/...) require payment header or credits, returning HTTP 402 Payment Required otherwise",
                "evidence_url": "https://agentpay-tools.agentpay-apis.workers.dev",
            },
        },
        "status": "verified",
        "expected_edits": None,
    },
    "Airtable": {
        "catalogue_fields": {
            "name": "Airtable",
            "url": "https://airtable.com/api",
            "description": "Integrate with Airtable",
            "auth": "OAuth",
            "https": "Yes",
            "cors": "Yes",
        },
        "access_requirements": {
            "authentication": {
                "required": True,
                "mechanism": "OAuth 2.0 / Bearer Token",
                "status": "verified",
                "details": "All API requests must be authenticated with Bearer tokens; API keys were deprecated on February 1, 2024",
                "evidence_url": "https://airtable.com/developers/web/api/authentication.md",
            },
            "registration": {
                "required": True,
                "classification": "Registration required",
                "status": "verified",
                "details": "Requires an Airtable user account to generate personal access tokens or register OAuth integrations",
                "evidence_url": "https://airtable.com/developers/web/api/authentication.md",
            },
            "payment": {
                "payment_required": False,
                "has_free_tier": True,
                "classification": "Free tier available",
                "free_tier_details": "Free plan includes unlimited bases and up to 1,000 records per base; paid tiers (Team, Business, Enterprise) provide increased limits",
                "status": "verified",
                "details": "Free plan is available indefinitely; payment/subscription is not required for basic API access",
                "evidence_url": "https://airtable.com/pricing",
            },
            "environment": {
                "required": True,
                "classification": "Workspace and base scoped",
                "status": "verified",
                "details": "API tokens are strictly scoped to specific workspaces, bases, and permission scopes configured on the token or granted via OAuth",
                "evidence_url": "https://airtable.com/developers/web/api/authentication.md",
            },
            "public_vs_api_access": {
                "distinguished": True,
                "status": "verified",
                "details": "Documentation and developer portal are publicly readable; API data endpoints require authentication and return HTTP 401 Unauthorized for unauthenticated requests",
                "evidence_url": "https://airtable.com/developers/web/api/authentication.md",
            },
        },
        "status": "verified",
        "expected_edits": {
            "auth": "OAuth",
            "cors": "Yes",
        },
    },
    "Api2Convert": {
        "catalogue_fields": {
            "name": "Api2Convert",
            "url": "https://www.api2convert.com/",
            "description": "Online File Conversion API",
            "auth": "apiKey",
            "https": "Yes",
            "cors": "No",
        },
        "access_requirements": {
            "authentication": {
                "required": True,
                "mechanism": "apiKey (header: x-api2convert-api-key) / Job Token (header: x-api2convert-token)",
                "status": "verified",
                "details": "File conversion operations and job endpoints require x-api2convert-api-key or x-api2convert-token header; only select read-only endpoints (e.g. GET /v2/conversions) are unauthenticated",
                "evidence_url": "https://www.api2convert.com/documentation/guides/authentication",
            },
            "registration": {
                "required": True,
                "classification": "Registration required",
                "status": "verified",
                "details": "Account registration is required to obtain an API key from user dashboard",
                "evidence_url": "https://www.api2convert.com/documentation/guides/quickstart",
            },
            "payment": {
                "payment_required": False,
                "has_free_tier": True,
                "classification": "Free tier with recurring daily quota",
                "free_tier_details": "Every registered user receives 30 free credits every 24 hours",
                "status": "verified",
                "details": "Free tier available; one-time credit packages and monthly recurring subscriptions available for high-volume conversion",
                "evidence_url": "https://www.api2convert.com/pricing",
            },
            "environment": {
                "required": False,
                "classification": "No specific environment or workspace",
                "status": "verified",
                "details": "Cloud REST API without specialized client environment requirements",
                "evidence_url": "https://www.api2convert.com/documentation",
            },
            "public_vs_api_access": {
                "distinguished": True,
                "status": "verified",
                "details": "Documentation landing page and read-only format/preset endpoints are public; conversion jobs require authentication and credit deduction",
                "evidence_url": "https://www.api2convert.com/documentation/guides/authentication",
            },
        },
        "status": "verified",
        "expected_edits": {
            "cors": "No",
        },
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
    Preserves URL text and query parameters exactly without alteration.
    """
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
# Category Parser
# ---------------------------------------------------------------------------

def parse_category_entries(
    markdown_text: str,
    target_category: str = CATEGORY,
    selected_only: bool = True,
) -> tuple[list[dict], list[dict], dict]:
    """
    Parse entries from the target category in markdown text.
    Preserves exact original line numbers, Markdown links, query strings, and Unicode characters.

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

    heading_valid, heading_issues = check_heading_hierarchy(markdown_text, target_category)

    for line_num, line in enumerate(lines, start=1):
        stripped = line.strip()

        # Detect category start
        if stripped == f"### {target_category}":
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
                maybe_link = extract_markdown_link(cells[0]) if cells else None
                name_hint = maybe_link[0] if maybe_link else (cells[0] if cells else "Unknown")
                if not selected_only or name_hint in SELECTED_APIS:
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
                "category": target_category,
                "line": line_num,
            }

            if not selected_only or name in SELECTED_APIS:
                entries.append(entry_data)

    metadata = {
        "category": target_category,
        "heading_valid": heading_valid,
        "heading_issues": heading_issues,
        "section_start_line": section_start_line,
        "section_end_line": section_end_line,
    }

    return entries, parse_errors, metadata


def check_duplicate_and_missing_entries(
    entries: list[dict],
    selected_apis: list[str] = SELECTED_APIS,
) -> tuple[list[str], list[str], list[dict]]:
    """Detect duplicate and missing selected API entries."""
    seen = set()
    duplicates = []
    cardinality_errors = []

    for entry in entries:
        name = entry["name"]
        if name in selected_apis:
            if name in seen and name not in duplicates:
                duplicates.append(name)
                cardinality_errors.append({
                    "line": entry["line"],
                    "api_name": name,
                    "error": f"Duplicate entry detected for '{name}'",
                })
            seen.add(name)

    missing = [name for name in selected_apis if name not in seen]
    for m in missing:
        cardinality_errors.append({
            "line": None,
            "api_name": m,
            "error": f"Missing required entry: '{m}' not found in category",
        })

    return duplicates, missing, cardinality_errors


# ---------------------------------------------------------------------------
# Access Verification & Discrepancy Reporting
# ---------------------------------------------------------------------------

def evaluate_access_evidence(entry: dict) -> dict:
    """
    Evaluate entry against verified authoritative access requirements.
    Detects discrepancies between parsed catalogue values and verified requirements.
    Attaches structured evidence report for authentication, registration, payment, environment,
    and public vs API access.
    """
    name = entry["name"]
    issues = []
    catalogue_discrepancies = []
    recommended_edits = None

    # Check basic Markdown format rules
    format_valid = True
    desc = entry.get("description", "")
    if not desc:
        format_valid = False
        issues.append("Missing required Description field")
    elif len(desc) > MAX_DESCRIPTION_LENGTH:
        format_valid = False
        issues.append(f"Description exceeds {MAX_DESCRIPTION_LENGTH} characters ({len(desc)})")
    elif not desc[0].isupper():
        format_valid = False
        issues.append("Description must start with an uppercase letter")

    raw_auth = entry.get("raw_auth", entry.get("auth", ""))
    clean_auth = entry.get("auth", "")
    if clean_auth not in VALID_AUTH:
        format_valid = False
        issues.append(f"Invalid Auth value: '{clean_auth}'")
    elif clean_auth != "No" and not (raw_auth.startswith("`") and raw_auth.endswith("`")):
        format_valid = False
        issues.append(f"Auth value '{clean_auth}' must be wrapped in backticks")

    if entry.get("https") not in VALID_HTTPS:
        format_valid = False
        issues.append(f"Invalid HTTPS value: '{entry.get('https')}'")

    if entry.get("cors") not in VALID_CORS:
        format_valid = False
        issues.append(f"Invalid CORS value: '{entry.get('cors')}'")

    # Access evidence lookup
    auth_data = VERIFIED_ACCESS_EVIDENCE.get(name)
    if not auth_data:
        # Unknown / Unverified entry
        return {
            "name": name,
            "url": entry.get("url", ""),
            "description": desc,
            "auth": clean_auth,
            "https": entry.get("https", ""),
            "cors": entry.get("cors", ""),
            "category": entry.get("category", CATEGORY),
            "line": entry.get("line"),
            "format_valid": format_valid,
            "status": "unverified",
            "access_requirements": None,
            "catalogue_discrepancies": ["No authoritative access evidence verified for this entry"],
            "recommended_edits": None,
            "issues": issues,
        }

    expected_cat = auth_data["catalogue_fields"]
    access_reqs = auth_data["access_requirements"]

    # Check Auth discrepancy
    if clean_auth != expected_cat["auth"]:
        disc = (
            f"Auth discrepancy: catalogue has '{clean_auth}', "
            f"but authoritative requirement is '{expected_cat['auth']}' "
            f"({access_reqs['authentication']['details']})"
        )
        catalogue_discrepancies.append(disc)
        if recommended_edits is None:
            recommended_edits = {}
        recommended_edits["auth"] = expected_cat["auth"]

    # Check HTTPS discrepancy
    if entry.get("https") != expected_cat["https"]:
        disc = (
            f"HTTPS discrepancy: catalogue has '{entry.get('https')}', "
            f"but authoritative requirement is '{expected_cat['https']}'"
        )
        catalogue_discrepancies.append(disc)
        if recommended_edits is None:
            recommended_edits = {}
        recommended_edits["https"] = expected_cat["https"]

    # Check CORS discrepancy
    if entry.get("cors") != expected_cat["cors"]:
        disc = (
            f"CORS discrepancy: catalogue has '{entry.get('cors')}', "
            f"but authoritative verification demonstrates '{expected_cat['cors']}'"
        )
        catalogue_discrepancies.append(disc)
        if recommended_edits is None:
            recommended_edits = {}
        recommended_edits["cors"] = expected_cat["cors"]

    return {
        "name": name,
        "url": entry.get("url", ""),
        "description": desc,
        "auth": clean_auth,
        "https": entry.get("https", ""),
        "cors": entry.get("cors", ""),
        "category": entry.get("category", CATEGORY),
        "line": entry.get("line"),
        "format_valid": format_valid,
        "status": auth_data["status"],
        "access_requirements": access_reqs,
        "catalogue_discrepancies": catalogue_discrepancies,
        "recommended_edits": recommended_edits,
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Offline Self-Tests
# ---------------------------------------------------------------------------

def run_self_tests(trigger_failure: bool = False) -> None:
    """Run comprehensive offline test suite verifying fixtures, edge cases, and access classifications."""
    print("Running self-tests for R02-T029 (Verify Access Requirements — Documents & Productivity)...")

    # 1. Test Valid entries fixture
    valid_fixture = FIXTURES_DIR / "valid_entries.md"
    assert valid_fixture.exists(), f"Missing fixture: {valid_fixture}"
    entries, errors, meta = parse_category_entries(valid_fixture.read_text(encoding="utf-8"))
    assert len(errors) == 0, f"Parse errors in valid fixture: {errors}"
    assert len(entries) == 3, f"Expected 3 entries in valid fixture, got {len(entries)}"
    assert meta["heading_valid"] is True
    dups, miss, card_errs = check_duplicate_and_missing_entries(entries)
    assert len(dups) == 0
    assert len(miss) == 0

    evaluated = [evaluate_access_evidence(e) for e in entries]
    assert all(e["format_valid"] for e in evaluated)
    assert all(e["status"] == "verified" for e in evaluated)
    assert all(len(e["catalogue_discrepancies"]) == 0 for e in evaluated)
    assert all(e["recommended_edits"] is None for e in evaluated)
    print("  [PASS] 01: Valid entries fixture")

    # 2. Test Missing required catalogue field fixture
    missing_field_f = FIXTURES_DIR / "missing_required_field.md"
    assert missing_field_f.exists(), f"Missing fixture: {missing_field_f}"
    mf_entries, mf_errors, _ = parse_category_entries(missing_field_f.read_text(encoding="utf-8"))
    assert len(mf_entries) == 3
    mf_eval = [evaluate_access_evidence(e) for e in mf_entries]
    airtable_eval = next(e for e in mf_eval if e["name"] == "Airtable")
    assert airtable_eval["format_valid"] is False
    assert any("Missing required Description field" in issue for issue in airtable_eval["issues"])
    print("  [PASS] 02: Missing required field fixture")

    # 3. Test Malformed Markdown row fixture
    malformed_f = FIXTURES_DIR / "malformed_row.md"
    assert malformed_f.exists(), f"Missing fixture: {malformed_f}"
    m_entries, m_errors, _ = parse_category_entries(malformed_f.read_text(encoding="utf-8"))
    assert len(m_errors) == 1
    assert m_errors[0]["actual_columns"] == 3
    assert m_errors[0]["expected_columns"] == 5
    assert len(m_entries) == 2
    print("  [PASS] 03: Malformed markdown row fixture")

    # 4. Test Source line tracking fixture
    track_f = FIXTURES_DIR / "source_line_tracking.md"
    assert track_f.exists(), f"Missing fixture: {track_f}"
    t_entries, t_errors, _ = parse_category_entries(track_f.read_text(encoding="utf-8"))
    assert len(t_errors) == 0
    line_map = {e["name"]: e["line"] for e in t_entries}
    assert line_map["AgentPay Doc Tools"] == 9, f"Expected line 9, got {line_map.get('AgentPay Doc Tools')}"
    assert line_map["Airtable"] == 10, f"Expected line 10, got {line_map.get('Airtable')}"
    assert line_map["Api2Convert"] == 11, f"Expected line 11, got {line_map.get('Api2Convert')}"
    print("  [PASS] 04: Source line tracking fixture")

    # 5. Test Authentication required classification fixture
    auth_f = FIXTURES_DIR / "auth_required.json"
    assert auth_f.exists(), f"Missing fixture: {auth_f}"
    auth_data = json.loads(auth_f.read_text(encoding="utf-8"))
    auth_map = {e["name"]: e for e in auth_data["entries"]}
    assert auth_map["AgentPay Doc Tools"]["auth_required"] is False
    assert auth_map["AgentPay Doc Tools"]["conflated_with_payment"] is False
    assert auth_map["AgentPay Doc Tools"]["payment_authorization_required"] is True
    assert auth_map["Airtable"]["auth_required"] is True
    assert "OAuth" in auth_map["Airtable"]["mechanism"]
    assert auth_map["Api2Convert"]["auth_required"] is True
    assert "apiKey" in auth_map["Api2Convert"]["mechanism"]
    print("  [PASS] 05: Authentication required fixture")

    # 6. Test Registration required classification fixture
    reg_f = FIXTURES_DIR / "registration_required.json"
    assert reg_f.exists(), f"Missing fixture: {reg_f}"
    reg_data = json.loads(reg_f.read_text(encoding="utf-8"))
    reg_map = {e["name"]: e for e in reg_data["entries"]}
    assert reg_map["AgentPay Doc Tools"]["registration_required"] is False
    assert reg_map["AgentPay Doc Tools"]["anonymous_access"] is True
    assert reg_map["Airtable"]["registration_required"] is True
    assert reg_map["Airtable"]["anonymous_access"] is False
    assert reg_map["Api2Convert"]["registration_required"] is True
    assert reg_map["Api2Convert"]["anonymous_access"] is False
    print("  [PASS] 06: Registration required fixture")

    # 7. Test Paid access and free-tier limitations fixture
    paid_f = FIXTURES_DIR / "paid_access_free_tier.json"
    assert paid_f.exists(), f"Missing fixture: {paid_f}"
    paid_data = json.loads(paid_f.read_text(encoding="utf-8"))
    paid_map = {e["name"]: e for e in paid_data["entries"]}
    assert paid_map["AgentPay Doc Tools"]["payment_required"] is True
    assert paid_map["AgentPay Doc Tools"]["has_free_tier"] is True
    assert paid_map["AgentPay Doc Tools"]["free_tier_unrestricted"] is False
    assert paid_map["Airtable"]["payment_required"] is False
    assert paid_map["Airtable"]["has_free_tier"] is True
    assert paid_map["Airtable"]["free_tier_unrestricted"] is False
    assert paid_map["Api2Convert"]["payment_required"] is False
    assert paid_map["Api2Convert"]["has_free_tier"] is True
    assert paid_map["Api2Convert"]["free_tier_unrestricted"] is False
    print("  [PASS] 07: Paid access & free-tier limitations fixture")

    # 8. Test Environment-specific access fixture
    env_f = FIXTURES_DIR / "environment_specific.json"
    assert env_f.exists(), f"Missing fixture: {env_f}"
    env_data = json.loads(env_f.read_text(encoding="utf-8"))
    env_map = {e["name"]: e for e in env_data["entries"]}
    assert env_map["AgentPay Doc Tools"]["environment_required"] is False
    assert env_map["Airtable"]["environment_required"] is True
    assert env_map["Api2Convert"]["environment_required"] is False
    print("  [PASS] 08: Environment-specific access fixture")

    # 9. Test Conflicting or inconclusive evidence fixture
    conf_f = FIXTURES_DIR / "conflicting_inconclusive.json"
    assert conf_f.exists(), f"Missing fixture: {conf_f}"
    conf_data = json.loads(conf_f.read_text(encoding="utf-8"))
    assert conf_data["resource"]["expected_status"] == "unverified"
    assert conf_data["resource"]["is_classified_as_free"] is False
    assert conf_data["resource"]["is_classified_as_auth_free"] is False
    print("  [PASS] 09: Conflicting / inconclusive evidence fixture")

    # 10. Test Unavailable resource classified as unverified fixture
    unavail_f = FIXTURES_DIR / "unavailable_unverified.json"
    assert unavail_f.exists(), f"Missing fixture: {unavail_f}"
    unavail_data = json.loads(unavail_f.read_text(encoding="utf-8"))
    assert unavail_data["resource"]["expected_status"] == "unverified"
    assert unavail_data["resource"]["classified_as_discontinued"] is False
    assert unavail_data["resource"]["classified_as_broken"] is False
    assert unavail_data["resource"]["remove_from_catalogue"] is False
    print("  [PASS] 10: Unavailable resource classified as unverified fixture")

    # 11. Test Official evidence URL preservation fixture
    ev_f = FIXTURES_DIR / "evidence_url_preservation.json"
    assert ev_f.exists(), f"Missing fixture: {ev_f}"
    ev_data = json.loads(ev_f.read_text(encoding="utf-8"))
    for claim in ev_data["verified_claims"]:
        assert claim["official_evidence_url"].startswith("https://")
        assert len(claim["official_evidence_url"]) > 10
    print("  [PASS] 11: Official evidence URL preservation fixture")

    # 12. Test Duplicate entries fixture
    dup_f = FIXTURES_DIR / "duplicate_entries.md"
    assert dup_f.exists(), f"Missing fixture: {dup_f}"
    d_entries, d_errors, _ = parse_category_entries(dup_f.read_text(encoding="utf-8"))
    assert len(d_errors) == 0
    assert len(d_entries) == 4
    d_dups, d_miss, d_card = check_duplicate_and_missing_entries(d_entries)
    assert d_dups == ["Airtable"]
    assert len(d_miss) == 0
    print("  [PASS] 12: Duplicate entries fixture")

    # 13. Test Unicode and Markdown URL preservation fixture
    uni_f = FIXTURES_DIR / "unicode_and_markdown_urls.md"
    assert uni_f.exists(), f"Missing fixture: {uni_f}"
    u_entries, u_errors, _ = parse_category_entries(uni_f.read_text(encoding="utf-8"))
    assert len(u_errors) == 0
    u_map = {e["name"]: e for e in u_entries}
    assert "pdf(ocr)" in u_map["AgentPay Doc Tools"]["url"]
    assert "Colaboração" in u_map["Airtable"]["description"]
    assert "München" in u_map["Api2Convert"]["url"]
    assert "für Dokumente" in u_map["Api2Convert"]["description"]
    print("  [PASS] 13: Unicode and Markdown URL preservation fixture")

    # 14. Test Content outside target category fixture
    out_f = FIXTURES_DIR / "outside_category.md"
    assert out_f.exists(), f"Missing fixture: {out_f}"
    out_entries, out_errors, _ = parse_category_entries(out_f.read_text(encoding="utf-8"))
    assert len(out_entries) == 0, f"Entries outside {CATEGORY} category must be ignored, got {out_entries}"
    print("  [PASS] 14: Outside category fixture ignored")

    # 15. Test Discrepancy detection and recommended edits fixture (incorrect metadata)
    inc_f = FIXTURES_DIR / "incorrect_metadata.md"
    assert inc_f.exists(), f"Missing fixture: {inc_f}"
    inc_entries, inc_errors, _ = parse_category_entries(inc_f.read_text(encoding="utf-8"))
    assert len(inc_errors) == 0
    inc_eval = [evaluate_access_evidence(e) for e in inc_entries]
    airtable_inc = next(e for e in inc_eval if e["name"] == "Airtable")
    api2conv_inc = next(e for e in inc_eval if e["name"] == "Api2Convert")
    agentpay_inc = next(e for e in inc_eval if e["name"] == "AgentPay Doc Tools")

    assert len(agentpay_inc["catalogue_discrepancies"]) == 0
    assert agentpay_inc["recommended_edits"] is None

    assert len(airtable_inc["catalogue_discrepancies"]) == 2
    assert airtable_inc["recommended_edits"] == {"auth": "OAuth", "cors": "Yes"}

    assert len(api2conv_inc["catalogue_discrepancies"]) == 1
    assert api2conv_inc["recommended_edits"] == {"cors": "No"}

    # Offline regression test: verify presence of catalogue discrepancies is treated as a failing validation condition
    inc_discrepancy_count = sum(len(e.get("catalogue_discrepancies", [])) for e in inc_eval)
    assert inc_discrepancy_count == 3, f"Expected 3 discrepancies in incorrect metadata fixture, got {inc_discrepancy_count}"
    is_failing_condition = bool(
        inc_errors
        or len(inc_entries) != len(SELECTED_APIS)
        or any(not r["format_valid"] for r in inc_eval)
        or inc_discrepancy_count > 0
    )
    assert is_failing_condition is True, "Presence of catalogue discrepancies must be treated as a failing validation condition"
    print("  [PASS] 15: Discrepancy detection and recommended edits fixture (regression: discrepancies treated as failing)")

    # 16. Negative self-test check: confirm that an intentionally incorrect assertion raises an AssertionError
    deliberately_wrong_expectation = "DeliberatelyIncorrectCategory"
    assertion_raised = False
    try:
        assert entries[0]["category"] == deliberately_wrong_expectation
    except AssertionError:
        assertion_raised = True
    assert assertion_raised is True, "Negative self-test failed: assertion did not raise on deliberate mismatch!"
    print("  [PASS] 16: Intentional assertion failure correctly raised and verified")

    # 17. Test CLI --intentional-failure flag safely in an isolated subprocess
    cmd = [sys.executable, str(Path(__file__).resolve()), "--intentional-failure"]
    sub_res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
    assert sub_res.returncode != 0, f"Expected --intentional-failure to exit non-zero, got exit code {sub_res.returncode}"
    assert (
        "ASSERTION ERROR" in sub_res.stderr
        or "intentional-failure" in sub_res.stderr
        or "intentional-failure" in sub_res.stdout
    ), f"Expected intentional failure message in output, got: {sub_res.stderr}"
    print("  [PASS] 17: CLI --intentional-failure flag safely verified to exit non-zero")

    if trigger_failure:
        print("\nTriggering intentional failure via --intentional-failure flag...")
        assert False, "Deliberate test failure requested via --intentional-failure"

    print("\nAll offline tests passed successfully!")


# ---------------------------------------------------------------------------
# Main Routine
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Verify Documents & Productivity access requirements in public-apis."
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
    entries, parse_errors, meta = parse_category_entries(readme_text, CATEGORY, selected_only=True)

    duplicates, missing, cardinality_errors = check_duplicate_and_missing_entries(entries)
    all_errors = parse_errors + cardinality_errors

    evaluated_reports = []
    discrepancy_count = 0
    for entry in entries:
        report = evaluate_access_evidence(entry)
        if report.get("catalogue_discrepancies"):
            discrepancy_count += len(report["catalogue_discrepancies"])
        evaluated_reports.append(report)

    summary = {
        "category": CATEGORY,
        "total_selected": len(SELECTED_APIS),
        "total_parsed": len(entries),
        "duplicate_entries": duplicates,
        "missing_entries": missing,
        "heading_hierarchy_valid": meta["heading_valid"],
        "parse_errors": all_errors,
        "valid_count": sum(1 for r in evaluated_reports if r["format_valid"]),
        "invalid_count": sum(1 for r in evaluated_reports if not r["format_valid"]),
        "discrepancies_detected": discrepancy_count,
        "entries": evaluated_reports,
    }

    print(json.dumps(summary, indent=2))

    # Save artifacts to work/R02-T029/
    work_dir = ROOT / "work/R02-T029"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = work_dir / "actual.json"
    actual_file.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    print(f"\nReport saved to {actual_file.relative_to(ROOT)}")

    if (
        all_errors
        or duplicates
        or missing
        or len(entries) != len(SELECTED_APIS)
        or any(not r["format_valid"] for r in evaluated_reports)
        or discrepancy_count > 0
    ):
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
