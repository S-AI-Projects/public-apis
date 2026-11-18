#!/usr/bin/env python3
"""
R02-T048 — Explain access requirements: Authentication & Authorization
Checker: validates Auth/HTTPS/CORS field values for the three assigned entries.

Assigned entries (README.md, commit 2676ca49):
  Line 306: Auth0     | apiKey | Yes | Yes
  Line 307: GetOTP    | apiKey | Yes | No
  Line 308: MojoAuth  | apiKey | Yes | Yes

Usage:
  python3 tools/course_checks/r02-t048.py              # live check against README.md
  python3 tools/course_checks/r02-t048.py --self-test  # offline fixture tests (no network)

Self-test exits 0 on success, non-zero on any assertion failure.
Running under python3 -O/-OO is detected and rejected with exit code 1.
"""

import sys
import os
import json
import pathlib

# ---------------------------------------------------------------------------
# Reject -O / -OO optimisation flags (they disable assert statements)
# ---------------------------------------------------------------------------
try:
    assert False  # noqa: B011
except AssertionError:
    pass  # normal mode — asserts are active
else:
    print("ERROR: Do not run this checker with -O or -OO flags.", file=sys.stderr)
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
SECTION_HEADING = "### Authentication & Authorization"
ASSIGNED = {
    "Auth0":    {"url": "https://auth0.com",            "auth": "`apiKey`", "https": "Yes", "cors": "Yes"},
    "GetOTP":   {"url": "https://otp.dev/en/docs/",     "auth": "`apiKey`", "https": "Yes", "cors": "No"},
    "MojoAuth": {"url": "https://mojoauth.com",         "auth": "`apiKey`", "https": "Yes", "cors": "Yes"},
}
ASSIGNED_LINES = {"Auth0": 306, "GetOTP": 307, "MojoAuth": 308}

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORK_DIR = REPO_ROOT / "work" / "R02-T048"

VALID_AUTH   = {"`apiKey`", "`OAuth`", "`X-Mashape-Key`", "`User-Agent`", "No"}
VALID_HTTPS  = {"Yes", "No"}
VALID_CORS   = {"Yes", "No", "Unknown"}


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------
def parse_section(lines, section_heading):
    """Return list of dicts {name, url, auth, https, cors, lineno}."""
    inside = False
    entries = []
    for lineno, raw in enumerate(lines, start=1):
        line = raw.rstrip("\n").rstrip("\r")
        if line.strip().startswith(section_heading):
            inside = True
            continue
        if inside:
            if (line.strip().startswith("### ") or line.strip().startswith("## ")) and line.strip() != section_heading:
                break
            if "Back to Index" in line or line.startswith("<"):
                continue
            # Must start with |
            if not line.startswith("|"):
                continue
            # Header / separator rows
            stripped = line.strip("|").strip()
            if stripped.startswith("API"):
                continue
            # Skip separator rows like |:---|:---|:---|:---|:---|
            if all(set(c.strip().lstrip(":").rstrip(":")) <= set("-") for c in stripped.split("|")):
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            # Expect 5 columns: Name | Description | Auth | HTTPS | CORS
            if len(parts) < 5:
                continue
            # Extract name and url from markdown link [name](url)
            cell0 = parts[0]
            if cell0.startswith("[") and "](" in cell0 and cell0.endswith(")"):
                bracket_end = cell0.index("](")
                name = cell0[1:bracket_end]
                url  = cell0[bracket_end+2:-1]
            else:
                name = cell0
                url  = ""
            # columns: 0=name/url, 1=description, 2=auth, 3=https, 4=cors
            entries.append({
                "name":   name,
                "url":    url,
                "auth":   parts[2],
                "https":  parts[3],
                "cors":   parts[4],
                "lineno": lineno,
            })
    return entries


def check_entries(entries):
    """Return list of error strings (empty = all OK)."""
    errors = []
    for e in entries:
        if e["auth"] not in VALID_AUTH:
            errors.append(f"Line {e['lineno']} [{e['name']}]: unknown Auth value '{e['auth']}'")
        if e["https"] not in VALID_HTTPS:
            errors.append(f"Line {e['lineno']} [{e['name']}]: unknown HTTPS value '{e['https']}'")
        if e["cors"] not in VALID_CORS:
            errors.append(f"Line {e['lineno']} [{e['name']}]: unknown CORS value '{e['cors']}'")
        if not e["url"]:
            errors.append(f"Line {e['lineno']} [{e['name']}]: missing markdown link / URL")
    return errors


# ---------------------------------------------------------------------------
# Self-test mode
# ---------------------------------------------------------------------------
def run_self_test():
    fixtures_dir = REPO_ROOT / "work" / "R02-T048" / "fixtures"
    results = []

    # --- Fixture 1: valid.md — three well-formed entries, all fields correct ---
    valid_md = fixtures_dir / "valid.md"
    lines = valid_md.read_text(encoding="utf-8").splitlines(keepends=True)
    entries = parse_section(lines, SECTION_HEADING)
    errors  = check_entries(entries)
    assert len(entries) == 3, f"valid.md: expected 3 entries, got {len(entries)}"
    assert errors == [],      f"valid.md: unexpected errors: {errors}"
    results.append({"fixture": "valid.md", "entries": len(entries), "errors": errors, "pass": True})

    # --- Fixture 2: bad-auth.md — entry with invalid Auth value ---
    bad_auth_md = fixtures_dir / "bad-auth.md"
    lines2 = bad_auth_md.read_text(encoding="utf-8").splitlines(keepends=True)
    entries2 = parse_section(lines2, SECTION_HEADING)
    errors2  = check_entries(entries2)
    assert any("Auth" in e or "unknown Auth" in e for e in errors2), \
        f"bad-auth.md: expected an Auth error, got: {errors2}"
    results.append({"fixture": "bad-auth.md", "entries": len(entries2), "errors": errors2, "pass": True})

    # --- Fixture 3: bad-https.md — entry with invalid HTTPS value ---
    bad_https_md = fixtures_dir / "bad-https.md"
    lines3 = bad_https_md.read_text(encoding="utf-8").splitlines(keepends=True)
    entries3 = parse_section(lines3, SECTION_HEADING)
    errors3  = check_entries(entries3)
    assert any("HTTPS" in e or "unknown HTTPS" in e for e in errors3), \
        f"bad-https.md: expected an HTTPS error, got: {errors3}"
    results.append({"fixture": "bad-https.md", "entries": len(entries3), "errors": errors3, "pass": True})

    # --- Fixture 4: no-link.md — entry with bare URL, no markdown link ---
    no_link_md = fixtures_dir / "no-link.md"
    lines4 = no_link_md.read_text(encoding="utf-8").splitlines(keepends=True)
    entries4 = parse_section(lines4, SECTION_HEADING)
    errors4  = check_entries(entries4)
    assert any("missing markdown link" in e for e in errors4), \
        f"no-link.md: expected a missing-link error, got: {errors4}"
    results.append({"fixture": "no-link.md", "entries": len(entries4), "errors": errors4, "pass": True})

    # --- Write results ---
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = WORK_DIR / "actual-results.json"
    out.write_text(json.dumps({"mode": "self-test", "fixtures": results}, indent=2), encoding="utf-8")
    print("Self-test passed: 4 fixtures verified (valid, bad-auth, bad-https, no-link).")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Live mode
# ---------------------------------------------------------------------------
def run_live():
    readme = REPO_ROOT / "README.md"
    if not readme.exists():
        print(f"ERROR: {readme} not found", file=sys.stderr)
        sys.exit(2)

    lines = readme.read_text(encoding="utf-8").splitlines(keepends=True)
    entries = parse_section(lines, SECTION_HEADING)
    errors  = check_entries(entries)

    # Report assigned entries
    assigned_found = {}
    for e in entries:
        if e["name"] in ASSIGNED:
            assigned_found[e["name"]] = e
            expected = ASSIGNED[e["name"]]
            status = "OK"
            detail = (f"auth={e['auth']} https={e['https']} cors={e['cors']}")
            mismatches = []
            for field in ("auth", "https", "cors"):
                if e[field] != expected[field]:
                    mismatches.append(f"{field}: got '{e[field]}', expected '{expected[field]}'")
            if mismatches:
                status = "MISMATCH"
                detail += " | " + "; ".join(mismatches)
            print(f"{status} line {e['lineno']}: {e['name']} | {detail}")

    # Warn for any missing assigned entries
    for name in ASSIGNED:
        if name not in assigned_found:
            print(f"WARNING: assigned entry '{name}' not found in section")

    if errors:
        for err in errors:
            print(f"ERROR: {err}")
        sys.exit(1)

    total = len(entries)
    print(f"Access-requirements check passed: {total} entries validated in 'Authentication & Authorization'.")

    # Save results
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out_data = {
        "mode": "live",
        "total_entries": total,
        "assigned": [e for e in entries if e["name"] in ASSIGNED],
        "errors": errors,
    }
    (WORK_DIR / "actual-results.json").write_text(json.dumps(out_data, indent=2), encoding="utf-8")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        run_live()
