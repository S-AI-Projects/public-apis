#!/usr/bin/env python3
"""
R02-T050 — Verify redirects: Anti-Malware
Checker: resolves redirect chains for assigned entries, classifying each hop as
200 OK, 3xx redirect (301/302/307/308), redirect loop, login wall, or timeout.
In --self-test mode uses offline fixtures only (no network).

Assigned entries (README.md, commit 2676ca49):
  Line 244: AbuseIPDB                         | https://docs.abuseipdb.com/
  Line 245: AlienVault Open Threat Exchange   | https://otx.alienvault.com/api
  Line 246: CAPEsandbox                       | https://capev2.readthedocs.io/en/latest/usage/api.html

Usage:
  python3 tools/course_checks/r02-t050.py --self-test  # offline fixture tests (no network)
  python3 tools/course_checks/r02-t050.py              # live redirect verification

Self-test exits 0 on success, non-zero on any assertion failure.
Running under python3 -O/-OO is detected and rejected with exit code 1.
"""

import sys
import json
import pathlib
import datetime

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
SECTION_HEADING = "### Anti-Malware"
ASSIGNED = {
    "AbuseIPDB": {
        "url":  "https://docs.abuseipdb.com/",
        "line": 244,
    },
    "AlienVault Open Threat Exchange (OTX)": {
        "url":  "https://otx.alienvault.com/api",
        "line": 245,
    },
    "CAPEsandbox": {
        "url":  "https://capev2.readthedocs.io/en/latest/usage/api.html",
        "line": 246,
    },
}

REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
WORK_DIR  = REPO_ROOT / "work" / "R02-T050"

MAX_REDIRECTS = 10  # redirect-loop threshold


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------
def classify_chain(chain):
    """
    chain: list of (status_code, url) tuples built by the caller.
    Returns one of: 'ok', 'redirect', 'loop', 'login_wall', 'timeout', 'error'.
    """
    if not chain:
        return "error"
    final_status, _ = chain[-1]
    redirect_statuses = {301, 302, 307, 308}

    # Detect loop: more than MAX_REDIRECTS hops or repeated URL
    if len(chain) > MAX_REDIRECTS:
        return "loop"
    seen_urls = [url for _, url in chain]
    if len(seen_urls) != len(set(seen_urls)):
        return "loop"

    # Classify by final status
    if final_status == 200:
        if len(chain) == 1:
            return "ok"
        # Had redirects before 200
        return "redirect"
    if final_status in {401, 403}:
        return "login_wall"
    if final_status in redirect_statuses:
        # Still redirecting at end — treat as unresolved redirect
        return "redirect"
    if final_status == 0:
        return "timeout"
    return "error"


# ---------------------------------------------------------------------------
# Offline fixture-based redirect resolver (for self-test)
# ---------------------------------------------------------------------------
def resolve_fixture(fixture):
    """
    fixture: dict with key 'chain': list of [status, url] pairs.
    Returns (chain_as_tuples, classification).
    """
    chain = [(int(h["status"]), h["url"]) for h in fixture["chain"]]
    return chain, classify_chain(chain)


# ---------------------------------------------------------------------------
# Live redirect resolver (urllib, HEAD only, timeout=10s)
# ---------------------------------------------------------------------------
def resolve_live(url, max_redirects=MAX_REDIRECTS):
    """
    Follow redirects manually using urllib so we can record each hop.
    Returns (chain, classification) where chain = [(status, url), ...].
    Uses HEAD requests; falls back to GET if HEAD returns 405.
    """
    import urllib.request
    import urllib.error

    chain = []
    current_url = url
    visited = set()

    for _ in range(max_redirects + 1):
        if current_url in visited:
            chain.append((0, current_url))
            return chain, "loop"
        visited.add(current_url)

        try:
            req = urllib.request.Request(
                current_url,
                method="HEAD",
                headers={"User-Agent": "Mozilla/5.0 (compatible; r02-t050-checker/1.0)"},
            )
            opener = urllib.request.build_opener(urllib.request.HTTPRedirectHandler())

            class NoRedirect(urllib.request.HTTPRedirectHandler):
                def redirect_request(self, req, fp, code, msg, headers, newurl):
                    return None

            no_redir_opener = urllib.request.build_opener(NoRedirect())
            try:
                resp = no_redir_opener.open(req, timeout=10)
                status = resp.status
                chain.append((status, current_url))
                if status not in {301, 302, 303, 307, 308}:
                    break
                next_url = resp.headers.get("Location", "")
                if not next_url:
                    break
                # Handle relative redirects
                if next_url.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(current_url)
                    next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
                current_url = next_url
            except urllib.error.HTTPError as e:
                # HEAD not allowed — try GET
                if e.code == 405:
                    req2 = urllib.request.Request(
                        current_url,
                        method="GET",
                        headers={"User-Agent": "Mozilla/5.0 (compatible; r02-t050-checker/1.0)"},
                    )
                    try:
                        resp2 = no_redir_opener.open(req2, timeout=10)
                        status = resp2.status
                        chain.append((status, current_url))
                        if status not in {301, 302, 303, 307, 308}:
                            break
                        next_url = resp2.headers.get("Location", "")
                        if not next_url:
                            break
                        if next_url.startswith("/"):
                            from urllib.parse import urlparse
                            parsed = urlparse(current_url)
                            next_url = f"{parsed.scheme}://{parsed.netloc}{next_url}"
                        current_url = next_url
                    except urllib.error.HTTPError as e2:
                        chain.append((e2.code, current_url))
                        break
                    except Exception:
                        chain.append((0, current_url))
                        return chain, "timeout"
                else:
                    chain.append((e.code, current_url))
                    break
        except OSError:
            chain.append((0, current_url))
            return chain, "timeout"

    if len(chain) > max_redirects:
        return chain, "loop"

    return chain, classify_chain(chain)


# ---------------------------------------------------------------------------
# Section parser
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
            if stripped.startswith("API"):
                continue
            if all(set(c.strip().lstrip(":").rstrip(":")) <= set("-") for c in stripped.split("|")):
                continue
            parts = [p.strip() for p in line.strip("|").split("|")]
            if len(parts) < 5:
                continue
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
# Self-test mode
# ---------------------------------------------------------------------------
def run_self_test():
    fixtures_dir = WORK_DIR / "fixtures"
    results = []

    # --- Fixture 1: direct-200.json — single hop, 200 OK ---
    f1 = json.loads((fixtures_dir / "direct-200.json").read_text(encoding="utf-8"))
    chain1, cls1 = resolve_fixture(f1)
    assert cls1 == "ok", f"direct-200.json: expected 'ok', got '{cls1}'"
    assert len(chain1) == 1, f"direct-200.json: expected 1 hop, got {len(chain1)}"
    results.append({"fixture": "direct-200.json", "chain": f1["chain"], "classification": cls1, "pass": True})

    # --- Fixture 2: redirect-301.json — 301 → 200 chain ---
    f2 = json.loads((fixtures_dir / "redirect-301.json").read_text(encoding="utf-8"))
    chain2, cls2 = resolve_fixture(f2)
    assert cls2 == "redirect", f"redirect-301.json: expected 'redirect', got '{cls2}'"
    assert len(chain2) == 2, f"redirect-301.json: expected 2 hops, got {len(chain2)}"
    results.append({"fixture": "redirect-301.json", "chain": f2["chain"], "classification": cls2, "pass": True})

    # --- Fixture 3: redirect-loop.json — repeated URL → loop ---
    f3 = json.loads((fixtures_dir / "redirect-loop.json").read_text(encoding="utf-8"))
    chain3, cls3 = resolve_fixture(f3)
    assert cls3 == "loop", f"redirect-loop.json: expected 'loop', got '{cls3}'"
    results.append({"fixture": "redirect-loop.json", "chain": f3["chain"], "classification": cls3, "pass": True})

    # --- Fixture 4: timeout.json — status 0 → timeout ---
    f4 = json.loads((fixtures_dir / "timeout.json").read_text(encoding="utf-8"))
    chain4, cls4 = resolve_fixture(f4)
    assert cls4 == "timeout", f"timeout.json: expected 'timeout', got '{cls4}'"
    results.append({"fixture": "timeout.json", "chain": f4["chain"], "classification": cls4, "pass": True})

    # --- Write results ---
    WORK_DIR.mkdir(parents=True, exist_ok=True)
    (WORK_DIR / "actual-results.json").write_text(
        json.dumps({"mode": "self-test", "fixtures": results}, indent=2), encoding="utf-8"
    )
    print("Self-test passed: 4 fixtures verified (direct-200, redirect-301, redirect-loop, timeout).")
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
    observed_date = datetime.date.today().isoformat()

    print("=== Redirect Verification: Anti-Malware ===")
    print(f"Date: {observed_date}")
    print(f"Total entries in section: {len(entries)}\n")

    assigned_results = []
    for entry in entries:
        if entry["name"] not in ASSIGNED:
            continue
        url = entry["url"]
        print(f"Checking line {entry['lineno']}: {entry['name']}")
        print(f"  URL: {url}")
        chain, classification = resolve_live(url)
        chain_desc = " → ".join(f"HTTP {s}" for s, _ in chain)
        print(f"  Chain: {chain_desc}")
        print(f"  Classification: {classification.upper()}")
        final_url = chain[-1][1] if chain else url
        if final_url != url:
            print(f"  Final URL: {final_url}")
        if classification == "redirect":
            print(f"  Recommendation: Update catalogue URL to final destination: {final_url}")
        elif classification == "loop":
            print(f"  Warning: Redirect loop detected — do NOT remove entry; label unverified")
        elif classification == "timeout":
            print(f"  Warning: Request timed out — do NOT remove entry; label unverified")
        elif classification == "login_wall":
            print(f"  Note: Login wall (4xx) — resource may require auth; label unverified")
        print()
        assigned_results.append({
            "name": entry["name"],
            "lineno": entry["lineno"],
            "url": url,
            "chain": [{"status": s, "url": u} for s, u in chain],
            "classification": classification,
            "final_url": final_url,
            "observed_date": observed_date,
        })

    WORK_DIR.mkdir(parents=True, exist_ok=True)
    out = {
        "mode": "live",
        "observed_date": observed_date,
        "total_entries": len(entries),
        "assigned": assigned_results,
    }
    (WORK_DIR / "actual-results.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print("Redirect verification complete.")
    sys.exit(0)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if "--self-test" in sys.argv:
        run_self_test()
    else:
        run_live()
