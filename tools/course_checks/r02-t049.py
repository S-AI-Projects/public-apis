#!/usr/bin/env python3
"""
R02-T049 — Document a repeatable maintenance pass: Entertainment
Checker: produces a one-command scoped maintenance report for the three assigned entries,
separating observed facts from recommendations, and generating stable output from fixtures.

Assigned entries (README.md, commit 2676ca49):
  Line 1032: Anycrap                    | apiKey | Yes | Yes
  Line 1033: Bucketlist Dream of the Day | No     | Yes | Yes
  Line 1034: chucknorris.io             | No     | Yes | Unknown

Usage:
  python3 tools/course_checks/r02-t049.py              # live maintenance report against README.md
  python3 tools/course_checks/r02-t049.py --self-test  # offline fixture tests (no network)

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
SECTION_HEADING = "### Entertainment"
ASSIGNED = {
    "Anycrap": {
        "url":   "https://anycrap.shop/developers",
        "auth":  "`apiKey`",
        "https": "Yes",
        "cors":  "Yes",
        "line":  1032,
    },
    "Bucketlist Dream of the Day": {
        "url":   "https://bucketlist.nl/samenwerken?lang=en#droom-van-de-dag",
        "auth":  "No",
        "https": "Yes",
        "cors":  "Yes",
        "line":  1033,
    },
    "chucknorris.io": {
        "url":   "https://api.chucknorris.io",
        "auth":  "No",
        "https": "Yes",
        "cors":  "Unknown",
        "line":  1034,
    },
}

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORK_DIR  = REPO_ROOT / "work" / "R02-T049"

VALID_AUTH  = {"`apiKey`", "`OAuth`", "`X-Mashape-Key`", "`User-Agent`", "No"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS  = {"Yes", "No", "Unknown"}


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
            if (line.strip().startswith("### ") or line.strip().startswith("## ")) and \
                    line.strip() != section_heading:
                break
            if "Back to Index" in line or line.startswith("<"):
                continue
            if not line.startswith("|"):
                continue
            stripped = line.strip("|").strip()
            # Skip header rows
            if stripped.startswith("API"):
                continue
            # Skip separator rows (all cells are dashes/colons)
            if all(set(c.strip().lstrip(":").rstrip(":")) <= set("-") for c in stripped.split("|")):
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) < 5:
                continue
            # columns: 0=name/url, 1=description, 2=auth, 3=https, 4=cors
            cell0 = parts[0]
            if cell0.startswith("[") and "](" in cell0 and cell0.endswith(")"):
                bracket_end = cell0.index("](")
                name = cell0[1:bracket_end]
                url  = cell0[bracket_end + 2:-1]
            else:
                name = cell0
                url  = ""
            entries.append({
                "name":   name,
                "url":    url,
                "auth":   parts[2],
                "https":  parts[3],
                "cors":   parts[4],
                "lineno": lineno,
            })
    return entries


# ---------------------------------------------------------------------------
# Maintenance checks
# ---------------------------------------------------------------------------
def maintenance_report(entries):
    """Return (facts, recommendations, errors) for each entry."""
    facts = []
    recommendations = []
    errors = []

    for e in entries:
        name, lineno = e["name"], e["lineno"]

        # Fact: field values as found
        facts.append(
            f"Line {lineno} [{name}]: auth={e['auth']} https={e['https']} cors={e['cors']} url={e['url'] or '(no link)'}"
        )

        # Validation errors
        if e["auth"] not in VALID_AUTH:
            errors.append(f"Line {lineno} [{name}]: invalid Auth value '{e['auth']}'")
        if e["https"] not in VALID_HTTPS:
            errors.append(f"Line {lineno} [{name}]: invalid HTTPS value '{e['https']}'")
        if e["cors"] not in VALID_CORS:
            errors.append(f"Line {lineno} [{name}]: invalid CORS value '{e['cors']}'")
        if not e["url"]:
            errors.append(f"Line {lineno} [{name}]: missing markdown link / URL")

        # Recommendations based on field values
        if e["cors"] == "Unknown":
            recommendations.append(
                f"Line {lineno} [{name}]: CORS is 'Unknown' — verify via browser DevTools or OPTIONS request"
            )
        if e["https"] == "No":
            recommendations.append(
                f"Line {lineno} [{name}]: HTTPS is 'No' — confirm whether TLS has since been added"
            )

    return facts, recommendations, errors


# ---------------------------------------------------------------------------
# Self-test mode
# ---------------------------------------------------------------------------
def run_self_test():
    fixtures_dir = WORK_DIR / "fixtures"
    results = []

    # --- Fixture 1: valid.md — 3 well-formed entries, all fields correct ---
    lines1 = (fixtures_dir / "valid.md").read_text(encoding="utf-8").splitlines(keepends=True)
    entries1 = parse_section(lines1, SECTION_HEADING)
    assert len(entries1) == 3, f"valid.md: expected 3 entries, got {len(entries1)}"
    facts1, recs1, errs1 = maintenance_report(entries1)
    assert errs1 == [], f"valid.md: unexpected errors: {errs1}"
    assert len(facts1) == 3, f"valid.md: expected 3 fact lines"
    results.append({"fixture": "valid.md", "entries": len(entries1), "errors": errs1,
                     "facts": facts1, "recommendations": recs1, "pass": True})

    # --- Fixture 2: unknown-cors.md — entry with CORS=Unknown → recommendation generated ---
    lines2 = (fixtures_dir / "unknown-cors.md").read_text(encoding="utf-8").splitlines(keepends=True)
    entries2 = parse_section(lines2, SECTION_HEADING)
    facts2, recs2, errs2 = maintenance_report(entries2)
    assert errs2 == [], f"unknown-cors.md: unexpected errors: {errs2}"
    assert any("CORS is 'Unknown'" in r for r in recs2), \
        f"unknown-cors.md: expected Unknown-CORS recommendation, got: {recs2}"
    results.append({"fixture": "unknown-cors.md", "entries": len(entries2), "errors": errs2,
                     "recommendations": recs2, "pass": True})

    # --- Fixture 3: bad-fields.md — entry with invalid Auth and HTTPS values → errors ---
    lines3 = (fixtures_dir / "bad-fields.md").read_text(encoding="utf-8").splitlines(keepends=True)
    entries3 = parse_section(lines3, SECTION_HEADING)
    facts3, recs3, errs3 = maintenance_report(entries3)
    assert any("invalid Auth" in e for e in errs3), \
        f"bad-fields.md: expected invalid-Auth error, got: {errs3}"
    results.append({"fixture": "bad-fields.md", "entries": len(entries3), "errors": errs3,
                     "facts": facts3, "pass": True})

    # --- Fixture 4: no-link.md — entry with bare URL → missing-link error ---
    lines4 = (fixtures_dir / "no-link.md").read_text(encoding="utf-8").splitlines(keepends=True)
    entries4 = parse_section(lines4, SECTION_HEADING)
    facts4, recs4, errs4 = maintenance_report(entries4)
    assert any("missing markdown link" in e for e in errs4), \
        f"no-link.md: expected missing-link error, got: {errs4}"
    results.append({"fixture": "no-link.md", "entries": len(entries4), "errors": errs4,
                     "facts": facts4, "pass": True})

    # --- Write results ---
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "actual-results.json").write_text(
        json.dumps({"mode": "self-test", "fixtures": results}, indent=2), encoding="utf-8"
    )
    print("Self-test passed: 4 fixtures verified (valid, unknown-cors, bad-fields, no-link).")
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
    facts, recommendations, errors = maintenance_report(entries)

    print("=== Maintenance Pass: Entertainment ===")
    print(f"\nTotal entries in section: {len(entries)}")

    print("\n--- Observed Facts (assigned entries) ---")
    assigned_found = {}
    for e in entries:
        if e["name"] in ASSIGNED:
            assigned_found[e["name"]] = e
            exp = ASSIGNED[e["name"]]
            match_str = ""
            mismatches = []
            for field in ("auth", "https", "cors"):
                if e[field] != exp[field]:
                    mismatches.append(f"{field}: got '{e[field]}', expected '{exp[field]}'")
            status = "MATCH" if not mismatches else "MISMATCH"
            print(f"  [{status}] Line {e['lineno']}: {e['name']}")
            print(f"           auth={e['auth']} https={e['https']} cors={e['cors']}")
            if mismatches:
                for m in mismatches:
                    print(f"           !! {m}")

    for name in ASSIGNED:
        if name not in assigned_found:
            print(f"  WARNING: assigned entry '{name}' not found in section")

    if recommendations:
        print("\n--- Recommendations ---")
        for r in recommendations:
            if any(e["name"] in r for e in entries if e["name"] in ASSIGNED):
                print(f"  * {r}")

    if errors:
        print("\n--- Errors ---")
        for err in errors:
            print(f"  ERROR: {err}")
        sys.exit(1)

    print("\nMaintenance pass completed: no field errors found.")

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out_data = {
        "mode": "live",
        "total_entries": len(entries),
        "assigned": [e for e in entries if e["name"] in ASSIGNED],
        "facts": facts,
        "recommendations": recommendations,
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
