#!/usr/bin/env python3
"""R02-T040 - Patent section checker for three selected public-apis entries.

Validates the ``Patent`` table in ``README.md`` against the contribution rules
described in ``CONTRIBUTING.md``.  Checks heading presence, exact table header
and separator, five-column row syntax, Markdown link URLs, Auth/HTTPS/CORS
metadata values, description character lengths (<=100), cell padding (rejecting
both missing and multiple spaces), and alphabetical row ordering.  Reports
dynamic 1-based source line numbers.

The three assigned entries are:
  - EPO          — https://developers.epo.org/
  - PatentsView  — https://patentsview.org/apis/purpose
  - TIPO         — https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00

Commands::

    python3 tools/course_checks/r02-t040.py --self-test
    python3 tools/course_checks/r02-t040.py
    python3 tools/course_checks/r02-t040.py --live
    python3 tools/course_checks/r02-t040.py --readme PATH
"""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

TASK_ID = "R02-T040"
ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = ROOT / "work" / TASK_ID
README_PATH = ROOT / "README.md"
FIXTURE_DIR = WORK_DIR / "fixtures"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"

SECTION_HEADING = "### Patent"

# Exact strings the README uses for the table header and separator.
EXPECTED_HEADER = "API | Description | Auth | HTTPS | CORS |"
EXPECTED_SEPARATOR = "|:---|:---|:---|:---|:---|"

ALLOWED_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
ALLOWED_HTTPS = {"Yes", "No"}
ALLOWED_CORS = {"Yes", "No", "Unknown"}

# Assigned entries with structured observations, historical context,
# unverified information, manual decisions, and recommended after values.
SELECTED_ENTRIES = [
    {
        "name": "EPO",
        "url": "https://developers.epo.org/",
        "auth": "OAuth",
        "https": "Yes",
        "cors": "Unknown",
        "observed_facts": (
            "European Patent Office Open Patent Services (OPS) v3.2 official documentation "
            "at https://developers.epo.org/ states user registration generates a Consumer Key "
            "and Consumer Secret. Token endpoint POST https://ops.epo.org/3.2/auth/accesstoken "
            "issues an OAuth 2.0 access token supplied as 'Authorization: Bearer <token>'. "
            "Served exclusively over HTTPS."
        ),
        "historical_info": (
            "OPS has operated as an OAuth 2.0 service across v2.x and v3.x releases, "
            "superseding earlier unauthenticated access interfaces."
        ),
        "unverified_info": (
            "CORS headers for third-party browser clients are undocumented in the OPS developer "
            "portal. Direct browser cross-origin requests remain unverified without live header capture."
        ),
        "manual_decisions": (
            "Retain existing catalogue metadata as-is ('OAuth', 'Yes', 'Unknown'). Accurately "
            "reflects OPS OAuth 2.0 client credentials requirement under CONTRIBUTING.md rules."
        ),
        "recommended_auth": "OAuth",
        "recommended_https": "Yes",
        "recommended_cors": "Unknown",
    },
    {
        "name": "PatentsView",
        "url": "https://patentsview.org/apis/purpose",
        "auth": "No",
        "https": "Yes",
        "cors": "Unknown",
        "observed_facts": (
            "Legacy API documentation at https://patentsview.org/apis/purpose and "
            "https://patentsview.org/apis/api-endpoints documented unauthenticated GET/POST access "
            "to https://api.patentsview.org/patents/query without any API key (Auth: 'No'). "
            "The newer PatentSearch API at https://search.patentsview.org/docs/ requires user registration "
            "and an 'X-Api-Key' HTTP header (Auth: 'apiKey'). USPTO announced migration of patent data "
            "dissemination services to the USPTO Open Data Portal at https://data.uspto.gov/ and "
            "https://api.uspto.gov/."
        ),
        "historical_info": (
            "PatentsView legacy API operated as an open, unauthenticated REST service. The newer "
            "PatentSearch API was introduced subsequently, and migration to the USPTO Open Data Portal "
            "is scheduled to supersede earlier dissemination platforms."
        ),
        "unverified_info": (
            "Exact decommission date for legacy unauthenticated endpoints vs transition phase is "
            "unverified externally; migration timeline to USPTO ODP remains in progress."
        ),
        "manual_decisions": (
            "Keep root README.md unchanged ('No', 'Yes', 'Unknown') for the legacy URL assigned. "
            "Per policy, do not apply new PatentSearch API key requirements to the legacy endpoint "
            "without version distinction. Document the legacy vs current distinction and USPTO migration "
            "separately in decisions.md."
        ),
        "recommended_auth": "No",
        "recommended_https": "Yes",
        "recommended_cors": "Unknown",
    },
    {
        "name": "TIPO",
        "url": "https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Unknown",
        "observed_facts": (
            "Taiwan Intellectual Property Office (經濟部智慧財產局) Gazette Open Data platform at "
            "https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00 provides patent gazette "
            "dataset API00. Developers register on TIPONet (https://tiponet.tipo.gov.tw/), authenticate with "
            "account credentials to obtain an API access token, and supply the token as a Bearer token in the "
            "Authorization header (or token parameter). Protocol is HTTPS."
        ),
        "historical_info": (
            "TIPO established the Gazette Open Data API under the Taiwan Executive Yuan Open Data initiative, "
            "providing programmatic REST access in place of physical and batch media distribution."
        ),
        "unverified_info": (
            "CORS headers for third-party browser clients and machine-readable OpenAPI specs for dataset "
            "API00 remain unverified externally on tiponet.tipo.gov.tw."
        ),
        "manual_decisions": (
            "Retain 'apiKey' classification. In CONTRIBUTING.md, 'apiKey' is defined as 'the API uses a "
            "private key string/token for authentication'. Because TIPO uses an issued private token rather "
            "than an OAuth 2.0 authorization server, 'apiKey' is the exact, proper classification."
        ),
        "recommended_auth": "apiKey",
        "recommended_https": "Yes",
        "recommended_cors": "Unknown",
    },
]

SELECTED_API_NAMES = {e["name"] for e in SELECTED_ENTRIES}


# ---------------------------------------------------------------------------
# Markdown link parser (handles balanced parens, escaped chars, trailing spaces)
# ---------------------------------------------------------------------------

def parse_md_link(text: str):
    """Return (display_text, url) from the first ``[text](url)`` in *text*.

    Handles:
    - Balanced parentheses inside the URL.
    - Escaped ``\\|`` inside the display text.
    - Query strings and percent-encoding.

    Returns ``(None, None)`` when no link is found.
    """
    bracket_start = text.find("[")
    if bracket_start == -1:
        return None, None

    depth = 0
    i = bracket_start
    bracket_end = -1
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "[":
            depth += 1
        elif ch == "]":
            depth -= 1
            if depth == 0:
                bracket_end = i
                break
        i += 1

    if bracket_end == -1 or bracket_end + 1 >= len(text) or text[bracket_end + 1] != "(":
        return None, None

    paren_start = bracket_end + 1
    depth = 0
    i = paren_start
    paren_end = -1
    while i < len(text):
        ch = text[i]
        if ch == "\\" and i + 1 < len(text):
            i += 2
            continue
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                paren_end = i
                break
        i += 1

    if paren_end == -1:
        return None, None

    display = text[bracket_start + 1 : bracket_end]
    url = text[paren_start + 1 : paren_end]
    return display, url


# ---------------------------------------------------------------------------
# Row parser & padding checker
# ---------------------------------------------------------------------------

def split_table_row(line: str):
    """Split a Markdown table row into stripped cell strings.

    Handles escaped pipes (``\\|``) inside cells. Returns an empty list
    when the line does not look like a table row.
    """
    s = line.strip()
    if not s.startswith("|"):
        return []
    placeholder = "\x00PIPE\x00"
    s = s.replace("\\|", placeholder)
    parts = s.split("|")
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.replace(placeholder, "|").strip() for p in parts]


def find_unescaped_pipes(line: str) -> list:
    """Return 0-based indices of all unescaped pipe characters in *line*."""
    pipes = []
    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            i += 2
            continue
        if line[i] == "|":
            pipes.append(i)
        i += 1
    return pipes


def has_exact_cell_padding(line: str) -> bool:
    """Check that every table cell has exactly one space on each side.

    Rejects:
    - Missing spaces: e.g. ``|cell|``, ``|[Name](URL) |``, ``| [Name](URL)|``
    - Multiple spaces: e.g. ``|  cell |``, ``| cell  |``
    """
    line = line.rstrip("\r\n")
    pipes = find_unescaped_pipes(line)
    if len(pipes) < 2:
        return False
    if pipes[0] != 0 or pipes[-1] != len(line) - 1:
        return False

    for j in range(len(pipes) - 1):
        segment = line[pipes[j] + 1 : pipes[j + 1]]
        # A cell with exact single space padding on either side must have length >= 3
        # (at least ' c ') and start/end with exactly one space.
        if len(segment) < 3:
            return False
        if not segment.startswith(" ") or segment.startswith("  "):
            return False
        if not segment.endswith(" ") or segment.endswith("  "):
            return False

    return True


# ---------------------------------------------------------------------------
# Validation Logic
# ---------------------------------------------------------------------------

def validate_readme(readme_text: str, source_label: str = "README.md"):
    """Validate the Patent section of *readme_text*.

    Returns ``(entries, errors, section_meta)`` where *entries* is a list of
    parsed entry dicts, *errors* is a list of error dicts, and *section_meta*
    records dynamic line positions.
    """
    lines = readme_text.splitlines()
    errors = []
    entries = []
    section_meta = {
        "source_label": source_label,
        "heading_line": None,
        "header_line": None,
        "separator_line": None,
        "row_count": 0,
    }

    # --- find heading ---
    heading_line = None
    for idx, raw in enumerate(lines, start=1):
        if raw.strip() == SECTION_HEADING:
            heading_line = idx
            break

    if heading_line is None:
        errors.append({
            "line": 0,
            "code": "missing_heading",
            "message": f"Heading '{SECTION_HEADING}' not found in {source_label}.",
        })
        return entries, errors, section_meta

    section_meta["heading_line"] = heading_line

    # --- find table header ---
    header_line_no = heading_line + 1
    if header_line_no > len(lines):
        errors.append({
            "line": header_line_no,
            "code": "missing_header",
            "message": "Table header line is missing after heading.",
        })
        return entries, errors, section_meta

    section_meta["header_line"] = header_line_no
    raw_header = lines[header_line_no - 1]
    if raw_header.strip() != EXPECTED_HEADER:
        errors.append({
            "line": header_line_no,
            "code": "bad_header",
            "message": (
                f"Unexpected table header.\n"
                f"  expected: {EXPECTED_HEADER!r}\n"
                f"  got:      {raw_header.strip()!r}"
            ),
        })

    # --- find separator ---
    sep_line_no = header_line_no + 1
    if sep_line_no > len(lines):
        errors.append({
            "line": sep_line_no,
            "code": "missing_separator",
            "message": "Table separator line is missing.",
        })
        return entries, errors, section_meta

    section_meta["separator_line"] = sep_line_no
    raw_sep = lines[sep_line_no - 1]
    if raw_sep.strip() != EXPECTED_SEPARATOR:
        errors.append({
            "line": sep_line_no,
            "code": "bad_separator",
            "message": (
                f"Unexpected table separator.\n"
                f"  expected: {EXPECTED_SEPARATOR!r}\n"
                f"  got:      {raw_sep.strip()!r}"
            ),
        })

    # --- parse data rows ---
    row_start = sep_line_no + 1
    for idx in range(row_start, len(lines) + 1):
        raw = lines[idx - 1]
        stripped = raw.strip()
        # End of section: blank line, new heading, or back-to-index marker.
        if not stripped or stripped.startswith("#") or stripped.startswith("**[⬆"):
            break
        # Skip HTML comments or annotations that are not table rows
        if stripped.startswith("<!--"):
            continue
        if not stripped.startswith("|"):
            continue

        cells = split_table_row(raw)
        if len(cells) != 5:
            errors.append({
                "line": idx,
                "code": "bad_column_count",
                "message": (
                    f"Row has {len(cells)} column(s), expected 5: {stripped!r}"
                ),
            })
            continue

        name_cell, desc_cell, auth_cell, https_cell, cors_cell = cells

        # Validate exact Markdown table-cell padding (rejects missing and multiple spaces)
        if not has_exact_cell_padding(raw):
            errors.append({
                "line": idx,
                "code": "bad_padding",
                "message": "Table cells must have exactly one space around each delimiter.",
            })

        # Description length <= 100 characters
        if len(desc_cell) > 100:
            errors.append({
                "line": idx,
                "code": "description_too_long",
                "message": (
                    f"Description has {len(desc_cell)} characters; "
                    "maximum allowed is 100."
                ),
            })

        # Parse link in name cell
        raw_name, api_url = parse_md_link(name_cell)
        if raw_name is None:
            errors.append({
                "line": idx,
                "code": "bad_link",
                "message": f"Name cell has no Markdown link: {name_cell!r}",
            })
            continue

        if not api_url:
            errors.append({
                "line": idx,
                "code": "empty_url",
                "message": f"Link URL is empty for entry '{raw_name}'.",
            })

        api_name = raw_name.strip()

        # Normalize and validate Auth
        norm_auth = auth_cell.strip("`")
        if auth_cell not in ALLOWED_AUTH and norm_auth not in ALLOWED_AUTH:
            errors.append({
                "line": idx,
                "code": "invalid_auth",
                "message": (
                    f"Invalid Auth value {auth_cell!r} for '{api_name}'. "
                    f"Allowed: {sorted(ALLOWED_AUTH)}"
                ),
            })

        if https_cell not in ALLOWED_HTTPS:
            errors.append({
                "line": idx,
                "code": "invalid_https",
                "message": (
                    f"Invalid HTTPS value {https_cell!r} for '{api_name}'. "
                    f"Allowed: {sorted(ALLOWED_HTTPS)}"
                ),
            })

        if cors_cell not in ALLOWED_CORS:
            errors.append({
                "line": idx,
                "code": "invalid_cors",
                "message": (
                    f"Invalid CORS value {cors_cell!r} for '{api_name}'. "
                    f"Allowed: {sorted(ALLOWED_CORS)}"
                ),
            })

        entries.append({
            "name": api_name,
            "raw_name": raw_name,
            "url": api_url,
            "auth": norm_auth,
            "raw_auth": auth_cell,
            "https": https_cell,
            "cors": cors_cell,
            "description": desc_cell,
            "line": idx,
        })

    section_meta["row_count"] = len(entries)

    # --- check alphabetical ordering ---
    names = [e["name"] for e in entries]
    for i in range(1, len(names)):
        if names[i - 1].casefold() > names[i].casefold():
            lo = entries[i - 1]["line"]
            li = entries[i]["line"]
            errors.append({
                "line": li,
                "code": "wrong_order",
                "message": (
                    f"Ordering error: '{names[i-1]}' (line {lo}) should come "
                    f"after '{names[i]}' (line {li}) alphabetically."
                ),
            })

    # --- check selected entries presence and expected metadata ---
    found_names = {e["name"] for e in entries}
    for sel in SELECTED_ENTRIES:
        if sel["name"] not in found_names:
            errors.append({
                "line": 0,
                "code": "missing_entry",
                "message": f"Selected entry '{sel['name']}' not found in section.",
            })
        else:
            matched = next(e for e in entries if e["name"] == sel["name"])
            for field in ("url", "auth", "https", "cors"):
                if matched.get(field) != sel[field]:
                    errors.append({
                        "line": matched["line"],
                        "code": f"wrong_{field}",
                        "message": (
                            f"'{sel['name']}' field '{field}': "
                            f"expected {sel[field]!r}, got {matched.get(field)!r}"
                        ),
                    })

    return entries, errors, section_meta


# ---------------------------------------------------------------------------
# Neighbor ordering validation
# ---------------------------------------------------------------------------

def validate_selected_neighbors(entries: list) -> list:
    """Explicitly validate selected APIs against immediate preceding and following entries."""
    selected_names = {e["name"] for e in SELECTED_ENTRIES}
    neighbor_errors = []

    for i, entry in enumerate(entries):
        name = entry["name"]
        if name not in selected_names:
            continue

        line = entry["line"]

        # Preceding entry
        if i > 0:
            prev = entries[i - 1]
            if prev["name"].casefold() > name.casefold():
                neighbor_errors.append({
                    "line": line,
                    "code": "neighbor_order_error",
                    "message": (
                        f"Selected entry '{name}' (line {line}) should come after "
                        f"preceding entry '{prev['name']}' (line {prev['line']}) alphabetically."
                    ),
                })

        # Following entry
        if i + 1 < len(entries):
            nxt = entries[i + 1]
            if name.casefold() > nxt["name"].casefold():
                neighbor_errors.append({
                    "line": line,
                    "code": "neighbor_order_error",
                    "message": (
                        f"Selected entry '{name}' (line {line}) should come before "
                        f"following entry '{nxt['name']}' (line {nxt['line']}) alphabetically."
                    ),
                })

    return neighbor_errors


# ---------------------------------------------------------------------------
# Deterministic Report Generator
# ---------------------------------------------------------------------------

def generate_report(entries: list, errors: list, section_meta: dict) -> str:
    """Generate a clean, deterministic, multi-section validation report.

    Strictly separates:
    - 1. Source facts & scope
    - 2. Existing catalogue metadata
    - 3. Official documentation observations
    - 4. Historical information & version distinctions
    - 5. Manual decisions & recommended metadata
    - 6. Unverified or inconclusive information
    - 7. Section-wide & neighbor structural validation
    - 8. Automated validation summary
    """
    lines = []
    lines.append("=" * 80)
    lines.append(f"{TASK_ID} Validation & Evidence Report: {SECTION_HEADING} Section")
    lines.append("=" * 80)

    # 1. Source facts & scope
    lines.append("\n[1. SOURCE FACTS & SCOPE]")
    lines.append(f"  Target file          : {section_meta.get('source_label', 'README.md')}")
    lines.append(f"  Target section       : {SECTION_HEADING}")
    lines.append(f"  Heading line (1-based): {section_meta.get('heading_line', 'N/A')}")
    lines.append(f"  Header line          : {section_meta.get('header_line', 'N/A')}")
    lines.append(f"  Separator line       : {section_meta.get('separator_line', 'N/A')}")
    lines.append(f"  Total data rows      : {section_meta.get('row_count', 0)}")

    # 2. Existing catalogue metadata
    lines.append("\n[2. EXISTING CATALOGUE METADATA]")
    for idx, sel in enumerate(SELECTED_ENTRIES, start=1):
        name = sel["name"]
        entry = next((e for e in entries if e["name"] == name), None)
        if entry:
            lines.append(
                f"  {idx}. {name:12s} (line {entry['line']:4d}): "
                f"Auth={entry['auth']!r:8s} HTTPS={entry['https']!r:5s} "
                f"CORS={entry['cors']!r:9s} URL={entry['url']}"
            )
        else:
            lines.append(f"  {idx}. {name:12s} : [MISSING OR MALFORMED]")

    # 3. Official documentation observations
    lines.append("\n[3. OFFICIAL DOCUMENTATION OBSERVATIONS]")
    for idx, sel in enumerate(SELECTED_ENTRIES, start=1):
        lines.append(f"  {idx}. {sel['name']}:")
        lines.append(f"     Documentation URL: {sel['url']}")
        lines.append(f"     Observed Facts   : {sel['observed_facts']}")

    # 4. Historical information & version distinctions
    lines.append("\n[4. HISTORICAL INFORMATION & VERSION DISTINCTIONS]")
    for idx, sel in enumerate(SELECTED_ENTRIES, start=1):
        lines.append(f"  {idx}. {sel['name']}:")
        lines.append(f"     Context : {sel['historical_info']}")

    # 5. Manual decisions & recommended metadata
    lines.append("\n[5. MANUAL DECISIONS & RECOMMENDED METADATA]")
    for idx, sel in enumerate(SELECTED_ENTRIES, start=1):
        lines.append(f"  {idx}. {sel['name']}:")
        lines.append(
            f"     Recommended Metadata : Auth={sel['recommended_auth']!r}, "
            f"HTTPS={sel['recommended_https']!r}, CORS={sel['recommended_cors']!r}"
        )
        lines.append(f"     Decision Rationale   : {sel['manual_decisions']}")

    # 6. Unverified or inconclusive information
    lines.append("\n[6. UNVERIFIED OR INCONCLUSIVE INFORMATION]")
    lines.append("  Policy Rule: Unverified external evidence or inconclusive reachability")
    lines.append("  probes are retained as inconclusive observations and do NOT become")
    lines.append("  confirmed catalogue metadata errors.")
    for idx, sel in enumerate(SELECTED_ENTRIES, start=1):
        lines.append(f"  - {sel['name']}: {sel['unverified_info']}")

    # 7. Section-wide & neighbor structural validation
    lines.append("\n[7. SECTION-WIDE & NEIGHBOR STRUCTURAL VALIDATION]")
    header_status = "PASS" if not any(e["code"] in ("missing_header", "bad_header") for e in errors) else "FAIL"
    sep_status = "PASS" if not any(e["code"] in ("missing_separator", "bad_separator") for e in errors) else "FAIL"
    col_status = "PASS" if not any(e["code"] == "bad_column_count" for e in errors) else "FAIL"
    pad_status = "PASS" if not any(e["code"] == "bad_padding" for e in errors) else "FAIL"
    len_status = "PASS" if not any(e["code"] == "description_too_long" for e in errors) else "FAIL"
    order_status = "PASS" if not any(e["code"] == "wrong_order" for e in errors) else "FAIL"

    lines.append(f"  Table header format         : [{header_status}]")
    lines.append(f"  Table separator format      : [{sep_status}]")
    lines.append(f"  Row column counts (5 cols)  : [{col_status}]")
    lines.append(f"  Markdown delimiter padding  : [{pad_status}] (rejects missing and multiple spaces)")
    lines.append(f"  Description length (<=100)  : [{len_status}]")
    lines.append(f"  Alphabetical row ordering   : [{order_status}] (case-insensitive)")

    neighbor_errors = validate_selected_neighbors(entries)
    if not neighbor_errors:
        for sel in SELECTED_ENTRIES:
            name = sel["name"]
            matched = next((e for e in entries if e["name"] == name), None)
            if matched:
                i = entries.index(matched)
                prev_info = entries[i - 1]["name"] if i > 0 else "None (first row)"
                next_info = entries[i + 1]["name"] if i + 1 < len(entries) else "None (last row)"
                lines.append(f"  - '{name}' (line {matched['line']}): preceded by '{prev_info}', followed by '{next_info}'")
        lines.append("  Neighbor ordering check     : [OK] (All selected entries ordered relative to neighbors)")
    else:
        lines.append("  Neighbor ordering check     : [FAIL]")
        for n_err in neighbor_errors:
            lines.append(f"    * line {n_err['line']}: {n_err['message']}")

    # 8. Automated validation summary
    selected_lines = {e["name"]: e["line"] for e in entries if e["name"] in SELECTED_API_NAMES}
    task_errors = [e for e in errors if e.get("line") in selected_lines.values() or e.get("code") == "missing_entry"]
    task_errors.extend(neighbor_errors)
    sec_errors = [e for e in errors if e.get("line") not in selected_lines.values() and e.get("code") != "missing_entry"]

    lines.append("\n[8. AUTOMATED VALIDATION SUMMARY]")
    lines.append(f"  Task-specific validation    : [{'PASS' if not task_errors else 'FAIL'}] ({len(task_errors)} error(s))")
    lines.append(f"  Section-wide validation     : [{'PASS' if not sec_errors else 'FAIL'}] ({len(sec_errors)} error(s))")

    total_error_count = len(errors) + len(neighbor_errors)
    if total_error_count == 0:
        lines.append(f"  Overall Validation Result   : PASSED (exit code 0)")
    else:
        lines.append(f"  Overall Validation Result   : FAILED (exit code 1) with {total_error_count} total error(s)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Live URL reachability probe (sequential, timeout, low concurrency, no creds)
# ---------------------------------------------------------------------------

def check_live_urls(timeout: float = 5.0) -> list:
    """Perform sequential HTTP requests for the 3 assigned documentation URLs.

    Rules:
    - Standard library urllib only.
    - Fixed URLs only; no arbitrary endpoints.
    - No credentials or API keys sent.
    - 5-second timeout, no retries.
    - Network failure is never treated as proof of API invalidity.
    """
    results = []
    print(f"\n[9. LIVE DOCUMENTATION PROBE] (timeout={timeout}s, no retries, no credentials):")
    print("  Notice: Network failure or inconclusive request is NOT proof that an API is invalid.")

    for item in SELECTED_ENTRIES:
        name = item["name"]
        url = item["url"]
        user_agent = "Mozilla/5.0 (compatible; PublicApisPatentChecker/1.0; standard-library)"
        req = urllib.request.Request(url, headers={"User-Agent": user_agent})
        req.get_method = lambda: "HEAD"

        status_label = "UNVERIFIED"
        detail = ""
        http_code = None

        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                http_code = resp.status
                if 200 <= resp.status < 400:
                    status_label = "REACHABLE"
                    detail = f"HTTP {resp.status} {resp.reason}"
                else:
                    detail = f"HTTP {resp.status} {resp.reason}"
        except urllib.error.HTTPError as e:
            http_code = e.code
            if e.code == 405:
                try:
                    req_get = urllib.request.Request(url, headers={"User-Agent": user_agent})
                    with urllib.request.urlopen(req_get, timeout=timeout) as resp_get:
                        http_code = resp_get.status
                        if 200 <= resp_get.status < 400:
                            status_label = "REACHABLE"
                            detail = f"GET HTTP {resp_get.status} {resp_get.reason}"
                        else:
                            detail = f"GET HTTP {resp_get.status} {resp_get.reason}"
                except Exception as ex_get:
                    detail = f"HEAD 405; GET probe: {ex_get}"
            else:
                detail = f"HTTP {e.code} {e.reason}"
        except Exception as e:
            detail = f"{type(e).__name__}: {e}"

        print(f"  - {name:15s} : [{status_label}] ({url})")
        print(f"      observation : {detail}")

        results.append({
            "name": name,
            "url": url,
            "status": status_label,
            "http_code": http_code,
            "detail": detail,
        })

    return results


# ---------------------------------------------------------------------------
# Self-test runner (strictly no assert statements; fails cleanly under -O/-OO)
# ---------------------------------------------------------------------------

def run_self_test() -> int:
    """Run all fixtures from manifest.json. Return 0 if all pass, 1 otherwise."""
    if not MANIFEST_PATH.exists():
        print(f"[ERROR] manifest.json not found: {MANIFEST_PATH}", file=sys.stderr)
        return 1

    with MANIFEST_PATH.open(encoding="utf-8") as fh:
        manifest = json.load(fh)

    total = 0
    passed = 0
    failures = []

    for item in manifest:
        fixture_name = item["fixture"]
        fixture_path = FIXTURE_DIR / fixture_name
        expected_exit = item.get("expected_exit", 0)
        expected_errors = item.get("expected_errors", [])
        expected_entries = item.get("expected_entries", [])

        total += 1

        if not fixture_path.exists():
            failures.append((fixture_name, [f"Fixture file not found: {fixture_path}"]))
            continue

        readme_text = fixture_path.read_text(encoding="utf-8")
        entries, errors, meta = validate_readme(readme_text, source_label=fixture_name)
        actual_exit = 0 if not errors else 1

        case_failures = []

        # Check exit code
        if actual_exit != expected_exit:
            case_failures.append(
                f"exit code: expected {expected_exit}, got {actual_exit}"
            )

        # Compare exact error counts
        actual_codes = [e["code"] for e in errors]
        expected_counts = Counter(expected_errors)
        actual_counts = Counter(actual_codes)

        if actual_counts != expected_counts:
            case_failures.append(
                f"error mismatch: expected {dict(expected_counts)}, "
                f"got {dict(actual_counts)}"
            )

        # Check expected entries (including dynamic line numbers)
        for exp_entry in expected_entries:
            match = next(
                (e for e in entries if e["name"] == exp_entry.get("name")), None
            )
            if match is None:
                case_failures.append(
                    f"expected entry '{exp_entry.get('name')}' not found in parsed output"
                )
                continue
            for field in ("url", "auth", "https", "cors", "line"):
                if field in exp_entry and match.get(field) != exp_entry[field]:
                    case_failures.append(
                        f"entry '{exp_entry['name']}' field '{field}': "
                        f"expected {exp_entry[field]!r}, got {match.get(field)!r}"
                    )

        if case_failures:
            failures.append((fixture_name, case_failures))
            status = "FAIL"
        else:
            passed += 1
            status = "PASS"

        print(f"[{status}] {fixture_name}")
        for msg in case_failures:
            print(f"       {msg}")

    print(f"\nSummary: {passed}/{total} fixtures passed.")
    return 0 if not failures else 1


# ---------------------------------------------------------------------------
# Live validation runner
# ---------------------------------------------------------------------------

def run_live(readme_path: Path = README_PATH, probe_urls: bool = False) -> int:
    """Validate README.md or custom file and print report. Return exit code."""
    if not readme_path.exists():
        print(f"[ERROR] Target file not found: {readme_path}", file=sys.stderr)
        return 1

    readme_text = readme_path.read_text(encoding="utf-8")
    entries, errors, section_meta = validate_readme(readme_text, source_label=str(readme_path))

    report = generate_report(entries, errors, section_meta)
    print(report)

    if probe_urls:
        check_live_urls()

    neighbor_errors = validate_selected_neighbors(entries)
    if errors or neighbor_errors:
        return 1
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"{TASK_ID} Patent section checker"
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline fixture tests from manifest.json and exit.",
    )
    group.add_argument(
        "--live",
        action="store_true",
        help="Run validation and perform sequential HTTP probe of assigned URLs.",
    )
    parser.add_argument(
        "--readme",
        "--input",
        dest="readme_path",
        type=Path,
        default=README_PATH,
        help="Path to README.md or fixture file to validate (default: repository README.md).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    return run_live(readme_path=args.readme_path, probe_urls=args.live)


if __name__ == "__main__":
    sys.exit(main())
