#!/usr/bin/env python3
"""R02-T039 - Books section checker for three selected public-apis entries.

Validates the ``Books`` table in ``README.md`` against the contribution rules
described in ``CONTRIBUTING.md``.  Checks heading presence, exact table header
and separator, five-column row syntax, Markdown link URLs, Auth/HTTPS/CORS
metadata values, description character lengths (<=100), cell padding, and
alphabetical row ordering.  Reports original 1-based README line numbers.

The three selected entries are:
  - A Bíblia Digital  — https://www.abibliadigital.com.br/en
  - Amanah Sunnah     — https://sunnah.amanahagent.cloud/developers
  - Bhagavad Gita     — https://docs.bhagavadgitaapi.in

Commands::

    python3 tools/course_checks/r02-t039.py --self-test
    python3 tools/course_checks/r02-t039.py
    python3 tools/course_checks/r02-t039.py --live

There is no arbitrary-URL option; the target list is fixed.
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

TASK_ID = "R02-T039"
ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = ROOT / "work" / TASK_ID
README_PATH = ROOT / "README.md"
FIXTURE_DIR = WORK_DIR / "fixtures"
MANIFEST_PATH = FIXTURE_DIR / "manifest.json"

SECTION_HEADING = "### Books"

# Exact strings the README uses for the table header and separator.
EXPECTED_HEADER = "API | Description | Auth | HTTPS | CORS |"
EXPECTED_SEPARATOR = "|:---|:---|:---|:---|:---|"

ALLOWED_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
ALLOWED_HTTPS = {"Yes", "No"}
ALLOWED_CORS = {"Yes", "No", "Unknown"}

# Selected API names exactly as they appear in the README.
SELECTED_API_NAMES = {"A Bíblia Digital", "Amanah Sunnah", "Bhagavad Gita"}

# Exact expected entries based on verified evidence:
# - A Bíblia Digital: Historical documentation confirms unauthenticated access was
#   permitted (limited to 20 req/hr/IP; free optional token lifted limit).
#   Therefore, historical Auth classification is 'No'.
# - Amanah Sunnah: Requires free 'apiKey' passed via X-API-Key header.
# - Bhagavad Gita: Catalogue lists 'apiKey', but external documentation is unverified
#   (domain for sale). Catalogue consistency validates the entry without inventing access rules.
SELECTED_ENTRIES = [
    {
        "name": "A Bíblia Digital",
        "url": "https://www.abibliadigital.com.br/en",
        "auth": "No",
        "https": "Yes",
        "cors": "No",
    },
    {
        "name": "Amanah Sunnah",
        "url": "https://sunnah.amanahagent.cloud/developers",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Yes",
    },
    {
        "name": "Bhagavad Gita",
        "url": "https://docs.bhagavadgitaapi.in",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Yes",
    },
]


# ---------------------------------------------------------------------------
# Markdown link parser  (handles balanced parens, encoded chars, query strings)
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

    # Walk to find matching ']'
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

    Handles escaped pipes (``\\|``) inside cells.  Returns an empty list
    when the line does not look like a table row.
    """
    s = line.strip()
    if not s.startswith("|"):
        return []
    # Replace escaped pipes with a placeholder, split, then restore.
    placeholder = "\x00PIPE\x00"
    s = s.replace("\\|", placeholder)
    parts = s.split("|")
    # Strip leading/trailing empty strings from outer pipes.
    if parts and parts[0].strip() == "":
        parts = parts[1:]
    if parts and parts[-1].strip() == "":
        parts = parts[:-1]
    return [p.replace(placeholder, "|").strip() for p in parts]


def has_exact_cell_padding(line: str) -> bool:
    """Check that every unescaped table delimiter has one space on each side."""
    line = line.rstrip("\r\n")

    if not line.startswith("| ") or not line.endswith(" |"):
        return False

    i = 0
    while i < len(line):
        if line[i] == "\\" and i + 1 < len(line):
            i += 2
            continue

        if line[i] == "|":
            if i == 0:
                if i + 1 >= len(line) or line[i + 1] != " ":
                    return False
            elif i == len(line) - 1:
                if line[i - 1] != " ":
                    return False
            elif line[i - 1] != " " or line[i + 1] != " ":
                return False

        i += 1

    return True


def utc_now() -> str:
    """Return ISO 8601 UTC timestamp."""
    return (
        datetime.now(timezone.utc)
        .isoformat(timespec="seconds")
        .replace("+00:00", "Z")
    )


# ---------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------

def validate_readme(readme_text: str, source_label: str = "README.md"):
    """Validate the Books section of *readme_text*.

    Returns ``(entries, errors)`` where *entries* is a list of dicts with
    ``name``, ``url``, ``auth``, ``https``, ``cors``, ``line`` and *errors*
    is a list of ``{"line": int, "code": str, "message": str}`` dicts.
    """
    lines = readme_text.splitlines()
    errors = []
    entries = []

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
            "message": f"Heading '{SECTION_HEADING}' not found.",
        })
        return entries, errors

    # --- find table header ---
    header_line_no = heading_line + 1
    if header_line_no > len(lines):
        errors.append({
            "line": header_line_no,
            "code": "missing_header",
            "message": "Table header line is missing after heading.",
        })
        return entries, errors

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
        return entries, errors

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
        # Skip non-row lines.
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

        # Validate exact Markdown table-cell padding.
        if not has_exact_cell_padding(raw):
            errors.append({
                "line": idx,
                "code": "bad_padding",
                "message": "Table cells must have exactly one space around each delimiter.",
            })

        # Description must not exceed 100 characters.
        if len(desc_cell) > 100:
            errors.append({
                "line": idx,
                "code": "description_too_long",
                "message": (
                    f"Description has {len(desc_cell)} characters; "
                    "maximum allowed is 100."
                ),
            })

        # Parse link in name cell.
        api_name, api_url = parse_md_link(name_cell)
        if api_name is None:
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
                "message": f"Link URL is empty for entry '{api_name}'.",
            })

        # Normalize and validate auth cell.
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
            "url": api_url,
            "auth": norm_auth,
            "raw_auth": auth_cell,
            "https": https_cell,
            "cors": cors_cell,
            "line": idx,
        })

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

    # --- check selected entries are present ---
    found_names = {e["name"] for e in entries}
    for sel in SELECTED_ENTRIES:
        if sel["name"] not in found_names:
            errors.append({
                "line": 0,
                "code": "missing_entry",
                "message": f"Selected entry '{sel['name']}' not found in section.",
            })
        else:
            # Verify metadata of selected entries.
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

    return entries, errors


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

        # Validate immediate preceding entry
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

        # Validate immediate following entry
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
# Live URL reachability check (sequential, timeout, no credentials)
# ---------------------------------------------------------------------------

def check_live_urls(timeout: float = 5.0) -> list:
    """Perform sequential HTTP requests for the 3 selected documentation URLs.

    Rules:
    - Standard library urllib only.
    - Fixed URLs only; no arbitrary endpoints.
    - No credentials or API keys sent.
    - 5-second timeout, no retries.
    - Any failure/non-2xx response is classified as unverified/inconclusive.
    """
    results = []
    print(f"\n{TASK_ID} - Live Documentation URL Probe (timeout={timeout}s, no retries):")
    print("  Note: Inconclusive or failed requests do NOT indicate that an API entry is broken.")

    for item in SELECTED_ENTRIES:
        name = item["name"]
        url = item["url"]
        user_agent = "Mozilla/5.0 (compatible; PublicApisChecker/1.0; standard-library)"
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
            # If HEAD is 405 Method Not Allowed, retry with GET once
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

        print(f"  {name:20s} [{status_label}] ({url})")
        print(f"      observation: {detail}")

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
    """Run all fixtures from manifest.json.  Return 0 if all pass, 1 otherwise."""
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
        entries, errors = validate_readme(readme_text, source_label=fixture_name)
        actual_exit = 0 if not errors else 1

        case_failures = []

        # Check exit code
        if actual_exit != expected_exit:
            case_failures.append(
                f"exit code: expected {expected_exit}, got {actual_exit}"
            )

        # Compare exact error counts, including duplicate error codes
        actual_codes = [e["code"] for e in errors]
        expected_counts = Counter(expected_errors)
        actual_counts = Counter(actual_codes)

        if actual_counts != expected_counts:
            case_failures.append(
                f"error mismatch: expected {dict(expected_counts)}, "
                f"got {dict(actual_counts)}"
            )

        # Check expected entries
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
    """Validate README.md and print a human-readable report. Return exit code."""
    if not readme_path.exists():
        print(f"[ERROR] README file not found: {readme_path}", file=sys.stderr)
        return 1

    readme_text = readme_path.read_text(encoding="utf-8")
    entries, errors = validate_readme(readme_text)

    # 1. Task-specific validation report
    selected_names = {e["name"] for e in SELECTED_ENTRIES}
    selected_lines = {}

    for entry in entries:
        if entry["name"] in selected_names:
            selected_lines[entry["name"]] = entry["line"]

    selected_errors = []

    # Find errors on selected rows
    for err in errors:
        line = err.get("line")
        if line and line in selected_lines.values():
            selected_errors.append(err)

    # Find selected entries that could not be parsed or were missing
    for selected in SELECTED_ENTRIES:
        name = selected["name"]
        if name not in selected_lines:
            selected_errors.append({
                "line": 0,
                "code": "missing_entry",
                "message": f"Selected entry '{name}' could not be validated.",
            })

    # Explicitly verify internal selected-entry ordering
    selected_entries = [
        entry for entry in entries
        if entry["name"] in selected_names
    ]

    for k in range(1, len(selected_entries)):
        if selected_entries[k - 1]["name"].casefold() > selected_entries[k]["name"].casefold():
            selected_errors.append({
                "line": selected_entries[k]["line"],
                "code": "selected_order_error",
                "message": (
                    f"Selected entry ordering error: '{selected_entries[k-1]['name']}' (line {selected_entries[k-1]['line']}) "
                    f"should come after '{selected_entries[k]['name']}' (line {selected_entries[k]['line']}) alphabetically."
                ),
            })

    # Explicitly validate selected APIs against their immediate neighbors
    neighbor_errors = validate_selected_neighbors(entries)
    selected_errors.extend(neighbor_errors)

    print(f"{TASK_ID} - Task-Specific Validation (Selected APIs):")

    for selected in SELECTED_ENTRIES:
        name = selected["name"]
        entry = next(
            (e for e in entries if e["name"] == name),
            None,
        )

        if entry:
            row_errors = [
                err for err in selected_errors
                if err.get("line") == entry["line"]
            ]

            status = "ERROR" if row_errors else "OK"

            print(
                f"  line {entry['line']:4d}  {name!r:25s} "
                f"auth={entry['auth']!r:10s} "
                f"https={entry['https']!r:6s} "
                f"cors={entry['cors']!r:8s} [{status}]"
            )

            for err in row_errors:
                print(f"      {err['code']}: {err['message']}")
        else:
            print(f"  {name}: [MISSING OR INVALID]")

    # Explicitly report selected ordering & neighbor status
    order_errors = [err for err in selected_errors if "order" in err.get("code", "")]
    if not order_errors:
        bg_entry = next((e for e in entries if e["name"] == "Bhagavad Gita"), None)
        bg_idx = entries.index(bg_entry) if bg_entry else -1
        following_info = ""
        if bg_idx >= 0 and bg_idx + 1 < len(entries):
            following_info = f", followed by '{entries[bg_idx + 1]['name']}'"
        print(f"  Selected-entry & neighbor ordering: [OK] (case-insensitive{following_info})")
    else:
        print(f"  Selected-entry & neighbor ordering: [ERROR] ({len(order_errors)} error(s))")

    if not selected_errors:
        print("  All selected APIs passed task-specific validation.")
    else:
        print(f"  Task-specific validation: [FAILED] ({len(selected_errors)} error(s))")

    # 2. Section-wide validation report
    section_wide_errors = [
        err for err in errors
        if err.get("line") not in selected_lines.values() and err.get("code") != "missing_entry"
    ]

    if section_wide_errors:
        print(f"\n{TASK_ID} - Section-Wide Validation ({SECTION_HEADING}):")
        for err in section_wide_errors:
            loc = f"line {err['line']}" if err.get("line") else "scope"
            print(f"  [{loc}] {err['code']}: {err['message']}")
        print(f"\nResult: FAILED (exit code 1) due to {len(section_wide_errors)} section-wide validation error(s).")
        return 1
    elif errors or selected_errors:
        print(f"\nResult: FAILED (exit code 1) due to task-specific validation error(s).")
        return 1

    print(f"\n{TASK_ID} - {SECTION_HEADING} — All checks passed.")

    if probe_urls:
        check_live_urls()

    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description=f"{TASK_ID} Books section checker"
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
        help="Run live validation and perform sequential HTTP probe of the 3 documentation URLs.",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=README_PATH,
        help="Path to README.md file to validate (default: repository README.md).",
    )
    args = parser.parse_args()

    if args.self_test:
        return run_self_test()
    return run_live(readme_path=args.readme, probe_urls=args.live)


if __name__ == "__main__":
    sys.exit(main())

