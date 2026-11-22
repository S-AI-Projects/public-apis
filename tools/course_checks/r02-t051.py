#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
R02-T051: Verify redirects — Currency Exchange
===============================================
Checker for the three assigned entries in the Currency Exchange section of README.md:
  - Currencylayer
  - Exchangerate.host
  - Exchangeratesapi.io

Usage:
  python3 tools/course_checks/r02-t051.py [--self-test] [--live] [--readme PATH]

Modes:
  --self-test   Run offline fixture-based tests. Exits non-zero on any failure.
  --live        Fetch the three entries over the network and write work/R02-T051/report.json.
  (default)     Print the parsed entries extracted from README.md and exit 0.

Standard library only. No third-party packages required.
"""

import argparse
import json
import os
import re
import socket
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TASK_ID = "R02-T051"
README_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "README.md",
)
FIXTURE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fixtures", "r02-t051")
WORK_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "work",
    TASK_ID,
)
REPORT_PATH = os.path.join(WORK_DIR, "report.json")

# The three entry names we care about (case-insensitive match against parsed title)
TARGET_NAMES = ["currencylayer", "exchangerate.host", "exchangeratesapi.io"]

MAX_HOPS = 5          # redirect budget per entry
REQUEST_TIMEOUT = 10  # seconds per individual request
MAX_TOTAL_REQUESTS = 20  # global cap across the whole run

USER_AGENT = (
    "Mozilla/5.0 (compatible; R02-T051-checker/1.0; "
    "+https://github.com/S-AI-Projects/public-apis)"
)

# Login-wall detection patterns
LOGIN_URL_PATTERNS = re.compile(
    r'/(login|signin|sign-in|auth|authenticate|account/login)',
    re.IGNORECASE,
)
LOGIN_BODY_PATTERNS = [
    re.compile(r'<input[^>]+type=["\']password["\']', re.IGNORECASE),
    re.compile(r'<form[^>]+action=["\'][^"\']*/(login|signin|sign-in|auth)["\']', re.IGNORECASE),
    re.compile(r'(please\s+sign\s+in|please\s+log\s+in|you\s+must\s+(be\s+)?log(ged)?\s+in)', re.IGNORECASE),
]

# Permanent redirect codes (recommend update_url)
PERMANENT_REDIRECT_CODES = {301, 308}
# Temporary redirect codes (recommend manual_review)
TEMPORARY_REDIRECT_CODES = {302, 303, 307}
ALL_REDIRECT_CODES = PERMANENT_REDIRECT_CODES | TEMPORARY_REDIRECT_CODES

# ---------------------------------------------------------------------------
# Data types (plain dicts with known keys — no dataclasses to stay lean)
# ---------------------------------------------------------------------------

# Entry dict keys: name, url, description, auth, https, cors, line_number (1-based)
# Result dict keys: entry, classification, hop_count, chain, final_url,
#                   recommendation, error_kind, error_detail, utm_flagged

# ---------------------------------------------------------------------------
# README parser
# ---------------------------------------------------------------------------

def parse_readme(readme_path: str) -> List[Dict]:
    """
    Read README.md, locate the '### Currency Exchange' section, and extract
    every table row that matches one of the three target entry names.

    Returns a list of entry dicts with keys:
      name, url, description, auth, https, cors, line_number (1-based)
    """
    with open(readme_path, encoding="utf-8") as fh:
        lines = fh.readlines()

    # Markdown link pattern:  [Title](URL)
    link_re = re.compile(r'\[([^\]]+)\]\(([^)]+)\)')
    # Table row pattern: | col | col | col | col | col |
    row_re = re.compile(r'^\s*\|(.+)\|\s*$')

    in_section = False
    entries = []

    for idx, raw_line in enumerate(lines):
        line = raw_line.rstrip('\n').rstrip('\r')
        line_number = idx + 1  # 1-based

        # Detect section start
        if re.match(r'^###\s+Currency Exchange\s*$', line):
            in_section = True
            continue

        # Detect section end (next ### heading)
        if in_section and re.match(r'^###', line):
            break

        if not in_section:
            continue

        # Skip header / separator rows
        if not row_re.match(line):
            continue
        if line.strip().startswith('|---') or line.strip().startswith('| ---') or \
                'API' in line and 'Description' in line and 'Auth' in line:
            continue

        # Split on | — keep inner segments
        segments = [s.strip() for s in line.split('|')[1:-1]]
        if len(segments) < 5:
            continue

        raw_title = segments[0]
        m = link_re.match(raw_title)
        if not m:
            continue

        name = m.group(1)
        url = m.group(2)

        # Only keep the three target entries
        if name.lower() not in TARGET_NAMES:
            continue

        entries.append({
            "name": name,
            "url": url,
            "description": segments[1],
            "auth": segments[2],
            "https": segments[3],
            "cors": segments[4],
            "line_number": line_number,
        })

    return entries


# ---------------------------------------------------------------------------
# HTTP fetch layer (injectable for offline testing)
# ---------------------------------------------------------------------------

class FetchResult:
    """Lightweight response container returned by the fetch function."""

    def __init__(self, status: int, headers: Dict[str, str], body: str, final_url: str):
        self.status = status
        self.headers = {k.lower(): v for k, v in headers.items()}
        self.body = body
        self.final_url = final_url

    def get_header(self, name: str) -> Optional[str]:
        return self.headers.get(name.lower())


class FetchError(Exception):
    """Wraps any network-level error with a kind label."""

    def __init__(self, kind: str, detail: str):
        super().__init__(detail)
        self.kind = kind   # 'timeout' | 'connection_error' | 'ssl_error' | 'unknown'
        self.detail = detail


def real_fetch(url: str, timeout: int = REQUEST_TIMEOUT) -> FetchResult:
    """
    Fetch a single URL without following redirects.
    Returns FetchResult. Raises FetchError on network-level failure.
    """
    req = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT},
        method="GET",
    )
    try:
        # We set redirect handler to NOT follow automatically
        opener = urllib.request.build_opener(NoRedirectHandler())
        with opener.open(req, timeout=timeout) as resp:
            body = resp.read(4096).decode("utf-8", errors="replace")
            status = resp.status
            headers = dict(resp.headers)
            return FetchResult(status=status, headers=headers, body=body, final_url=url)

    except urllib.error.HTTPError as exc:
        # HTTPError is raised for 4xx/5xx but also for redirect responses
        # when no redirect handler is in place — treat as response
        body_bytes = exc.read(4096) if exc.fp else b""
        body = body_bytes.decode("utf-8", errors="replace")
        return FetchResult(
            status=exc.code,
            headers=dict(exc.headers),
            body=body,
            final_url=url,
        )

    except socket.timeout:
        raise FetchError("timeout", f"Request to {url} timed out after {timeout}s")

    except urllib.error.URLError as exc:
        reason = str(exc.reason)
        if "timed out" in reason.lower() or isinstance(exc.reason, socket.timeout):
            raise FetchError("timeout", f"Request to {url} timed out: {reason}")
        if "ssl" in reason.lower() or "certificate" in reason.lower():
            raise FetchError("ssl_error", f"SSL error for {url}: {reason}")
        raise FetchError("connection_error", f"Connection error for {url}: {reason}")

    except Exception as exc:
        raise FetchError("unknown", f"Unexpected error for {url}: {exc}")


class NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevent urllib from auto-following redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # Return None to suppress automatic redirect

    def http_error_301(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_302(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_303(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_307(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)

    def http_error_308(self, req, fp, code, msg, headers):
        raise urllib.error.HTTPError(req.full_url, code, msg, headers, fp)


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def _is_login_wall(status: int, headers: Dict[str, str], body: str, url: str) -> bool:
    """Return True if the response looks like a login wall."""
    if status in (401, 403):
        return True
    if LOGIN_URL_PATTERNS.search(url):
        for pattern in LOGIN_BODY_PATTERNS:
            if pattern.search(body):
                return True
    if status == 200:
        for pattern in LOGIN_BODY_PATTERNS:
            if pattern.search(body):
                return True
    return False


def classify_url(
    start_url: str,
    fetch_fn: Callable[[str], FetchResult],
    max_hops: int = MAX_HOPS,
    request_counter: Optional[List[int]] = None,
    max_total: int = MAX_TOTAL_REQUESTS,
) -> Dict:
    """
    Walk the redirect chain for start_url with a bounded request budget.

    Returns a result dict with keys:
      classification, hop_count, chain, final_url, recommendation,
      error_kind, error_detail, utm_flagged
    """
    chain = []          # list of (url, status) tuples visited
    seen_urls = set()   # for loop detection
    current_url = start_url
    hop_count = 0
    utm_flagged = "?utm_" in start_url or "&utm_" in start_url

    if request_counter is None:
        request_counter = [0]

    def _result(classification, final_url=None, error_kind=None, error_detail=None,
                recommendation=None):
        if recommendation is None:
            recommendation = _recommend(classification, start_url, final_url)
        return {
            "classification": classification,
            "hop_count": hop_count,
            "chain": chain,
            "final_url": final_url,
            "recommendation": recommendation,
            "error_kind": error_kind,
            "error_detail": error_detail,
            "utm_flagged": utm_flagged,
        }

    while True:
        # Global request cap
        if request_counter[0] >= max_total:
            return _result("too_many_hops", error_detail="Global request cap reached")

        # Loop detection before fetching
        if current_url in seen_urls:
            chain.append((current_url, "LOOP"))
            return _result("redirect_loop")

        seen_urls.add(current_url)
        request_counter[0] += 1

        try:
            resp = fetch_fn(current_url)
        except FetchError as exc:
            chain.append((current_url, exc.kind.upper()))
            kind = exc.kind
            if kind == "timeout":
                return _result("transient_failure", error_kind="timeout", error_detail=exc.detail)
            elif kind == "ssl_error":
                return _result("transient_failure", error_kind="ssl_error", error_detail=exc.detail)
            elif kind == "connection_error":
                return _result("transient_failure", error_kind="connection_error", error_detail=exc.detail)
            else:
                return _result("transient_failure", error_kind="unknown", error_detail=exc.detail)

        chain.append((current_url, resp.status))

        # Check for login wall (before 2xx/redirect branching)
        if _is_login_wall(resp.status, resp.headers, resp.body, current_url):
            return _result("login_wall", final_url=current_url if resp.status == 200 else None)

        # Successful response
        if resp.status in (200, 204):
            if hop_count == 0:
                return _result("ok", final_url=current_url)
            else:
                # Determine if the chain was permanent or temporary
                was_permanent = all(
                    s in PERMANENT_REDIRECT_CODES
                    for _, s in chain[:-1]  # exclude the final 200
                    if isinstance(s, int) and s in ALL_REDIRECT_CODES
                )
                classification = "moved_permanent" if was_permanent else "moved_temporary"
                return _result(classification, final_url=current_url)

        # Redirect response
        if resp.status in ALL_REDIRECT_CODES:
            location = resp.get_header("location")
            if not location:
                return _result("needs_manual_review",
                               error_detail=f"Redirect {resp.status} with no Location header")

            # Resolve relative Location
            location = urllib.parse.urljoin(current_url, location)

            # Check if the redirect target looks like a login wall
            if LOGIN_URL_PATTERNS.search(location):
                hop_count += 1
                chain.append((location, "LOGIN_REDIRECT"))
                return _result("login_wall", final_url=location)

            hop_count += 1

            # Hop budget exceeded
            if hop_count >= max_hops:
                return _result("too_many_hops",
                               error_detail=f"Exceeded {max_hops} hops without reaching a final response")

            current_url = location
            continue

        # 4xx errors (excluding 401/403 handled above, 429 handled below)
        if resp.status == 429:
            return _result("transient_failure", error_kind="rate_limited",
                           error_detail=f"HTTP 429 Too Many Requests")

        if 500 <= resp.status <= 599:
            return _result("transient_failure", error_kind="server_error",
                           error_detail=f"HTTP {resp.status}")

        if 400 <= resp.status <= 499:
            return _result("client_error", error_kind="http_error",
                           error_detail=f"HTTP {resp.status}")

        # Anything else
        return _result("needs_manual_review",
                       error_detail=f"Unexpected status {resp.status}")


def _recommend(classification: str, original_url: str, final_url: Optional[str]) -> str:
    """Map classification → recommendation."""
    if classification == "ok":
        return "keep"
    if classification == "moved_permanent":
        # Only recommend update_url if the final URL is meaningfully different
        if final_url and final_url.rstrip("/") != original_url.rstrip("/"):
            return "update_url"
        return "keep"
    # Everything else: flag for a human
    return "manual_review"


# ---------------------------------------------------------------------------
# Check a single entry
# ---------------------------------------------------------------------------

def check_entry(
    entry: Dict,
    fetch_fn: Callable[[str], FetchResult],
    request_counter: Optional[List[int]] = None,
) -> Dict:
    """Run classify_url for one parsed entry and return a full result dict."""
    result = classify_url(
        start_url=entry["url"],
        fetch_fn=fetch_fn,
        request_counter=request_counter,
    )
    return {
        "entry_name": entry["name"],
        "entry_url": entry["url"],
        "entry_line_number": entry["line_number"],
        "entry_auth": entry["auth"],
        "entry_https": entry["https"],
        "entry_cors": entry["cors"],
        "entry_description": entry["description"],
        **result,
    }


# ---------------------------------------------------------------------------
# Offline fixture loader
# ---------------------------------------------------------------------------

def _load_fixture(fixture_name: str) -> Dict:
    path = os.path.join(FIXTURE_DIR, fixture_name)
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _make_fixture_fetch(steps: List[Dict]) -> Callable[[str], FetchResult]:
    """
    Build a fetch function backed by a fixture's step list.
    Each step maps a URL to a response or an error.
    Unknown URLs raise a FetchError('connection_error').
    """
    step_map: Dict[str, Dict] = {step["url"]: step for step in steps}
    call_order: List[str] = []  # track call sequence for loop detection tests

    def fixture_fetch(url: str) -> FetchResult:
        call_order.append(url)
        step = step_map.get(url)
        if step is None:
            raise FetchError("connection_error", f"No fixture step for URL: {url}")

        err = step.get("error")
        if err == "timeout":
            raise FetchError("timeout", step.get("error_detail", "timed out"))
        if err == "connection_error":
            raise FetchError("connection_error", step.get("error_detail", "connection error"))

        resp_data = step["response"]
        return FetchResult(
            status=resp_data["status"],
            headers=resp_data.get("headers", {}),
            body=resp_data.get("body", ""),
            final_url=url,
        )

    return fixture_fetch


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

class _AssertionFailed(Exception):
    pass


def _assert_eq(label: str, expected, actual):
    if expected != actual:
        raise _AssertionFailed(
            f"FAIL [{label}]: expected {expected!r}, got {actual!r}"
        )


def run_self_test(verbose: bool = True) -> int:
    """
    Run all offline fixture tests. Returns 0 on success, 1 on any failure.
    Also runs the negative-test subprocess proof and reports its exit code.
    """
    failures = []

    def run_case(fixture_file: str, case_label: str, entry_name: str = "Test Entry",
                 entry_url_override: Optional[str] = None):
        fixture = _load_fixture(fixture_file)
        steps = fixture["steps"]
        expected = fixture["expected"]
        entry_url = entry_url_override or steps[0]["url"]

        fetch_fn = _make_fixture_fetch(steps)
        fake_entry = {
            "name": entry_name,
            "url": entry_url,
            "description": "Test description",
            "auth": "No",
            "https": "Yes",
            "cors": "Unknown",
            "line_number": 1,
        }
        result = check_entry(fake_entry, fetch_fn)

        try:
            _assert_eq(f"{case_label}: classification",
                       expected["classification"], result["classification"])
            _assert_eq(f"{case_label}: hop_count",
                       expected["hop_count"], result["hop_count"])
            if expected.get("final_url") is not None:
                _assert_eq(f"{case_label}: final_url",
                           expected["final_url"], result["final_url"])
            _assert_eq(f"{case_label}: recommendation",
                       expected["recommendation"], result["recommendation"])
            if verbose:
                print(f"  PASS  {case_label}")
        except _AssertionFailed as exc:
            failures.append(str(exc))
            if verbose:
                print(f"  {exc}")

    print("=" * 60)
    print(f"R02-T051 self-test — {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    # ------------------------------------------------------------------ #
    # Positive fixture tests
    # ------------------------------------------------------------------ #
    print("\n[1] Direct 200 OK")
    run_case("fixture_200.json", "200 OK")

    print("\n[2] 301 → 200 (moved permanently)")
    run_case("fixture_301_to_200.json", "301→200")

    print("\n[3] 302 → 200 (moved temporarily)")
    run_case("fixture_302_to_200.json", "302→200")

    print("\n[4] 308 → 200 (permanent redirect, method-preserving)")
    run_case("fixture_308_to_200.json", "308→200")

    print("\n[5] Redirect loop")
    run_case("fixture_redirect_loop.json", "redirect loop")

    print("\n[6] Too many hops (exceeds MAX_HOPS=5)")
    # We need to present the entry URL as the first hop URL
    fix = _load_fixture("fixture_too_many_hops.json")
    fetch_fn = _make_fixture_fetch(fix["steps"])
    fake_entry = {
        "name": "TooManyHops", "url": fix["steps"][0]["url"],
        "description": "Test", "auth": "No", "https": "Yes", "cors": "Yes",
        "line_number": 1,
    }
    result = check_entry(fake_entry, fetch_fn)
    try:
        _assert_eq("too_many_hops: classification", "too_many_hops", result["classification"])
        print("  PASS  too many hops")
    except _AssertionFailed as exc:
        failures.append(str(exc))
        print(f"  {exc}")

    print("\n[7] Timeout")
    run_case("fixture_timeout.json", "timeout")

    print("\n[8] 5xx server error")
    run_case("fixture_5xx.json", "5xx")

    print("\n[9] 429 rate limited")
    run_case("fixture_429.json", "429")

    print("\n[10] Connection error")
    run_case("fixture_connection_error.json", "connection error")

    print("\n[11] Login wall — 200 with login form")
    run_case("fixture_login_wall_form.json", "login wall (form)")

    print("\n[12] Login wall — 401 Unauthorized")
    run_case("fixture_login_wall_401.json", "login wall (401)")

    print("\n[13] Login wall — 403 Forbidden")
    run_case("fixture_login_wall_403.json", "login wall (403)")

    print("\n[14] Login wall — redirect to /login URL")
    run_case("fixture_login_wall_redirect.json", "login wall (redirect)")

    print("\n[15] Client error — 404 Not Found")
    run_case("fixture_client_error_404.json", "404 client error")

    # ------------------------------------------------------------------ #
    # README parser smoke test
    # ------------------------------------------------------------------ #
    print("\n[16] README parser — extracts exactly 3 target entries")
    try:
        readme_path = README_DEFAULT
        if os.path.exists(readme_path):
            entries = parse_readme(readme_path)
            _assert_eq("parser: entry count", 3, len(entries))
            names_found = [e["name"].lower() for e in entries]
            for expected_name in TARGET_NAMES:
                if expected_name not in names_found:
                    raise _AssertionFailed(
                        f"FAIL [parser]: '{expected_name}' not found in parsed entries"
                    )
            for e in entries:
                if e["line_number"] < 1:
                    raise _AssertionFailed(
                        f"FAIL [parser]: line_number for '{e['name']}' is not positive"
                    )
            print("  PASS  README parser (3 entries found, all have line numbers)")
        else:
            print(f"  SKIP  README not found at {readme_path}")
    except _AssertionFailed as exc:
        failures.append(str(exc))
        print(f"  {exc}")

    # ------------------------------------------------------------------ #
    # Negative-test subprocess proof (Amendment 8)
    # ------------------------------------------------------------------ #
    print("\n[17] Negative-test proof (subprocess — MUST exit non-zero)")
    neg_exit = _run_negative_test_subprocess()
    if neg_exit != 0:
        print(f"  PASS  negative test exited with code {neg_exit} (non-zero ✓)")
    else:
        msg = f"FAIL [negative test]: expected non-zero exit, got 0"
        failures.append(msg)
        print(f"  {msg}")

    # ------------------------------------------------------------------ #
    # Summary
    # ------------------------------------------------------------------ #
    print("\n" + "=" * 60)
    if failures:
        print(f"RESULT: FAILED — {len(failures)} assertion(s) failed")
        for f in failures:
            print(f"  • {f}")
        return 1
    else:
        print(f"RESULT: ALL TESTS PASSED (17 checks)")
        return 0


def _run_negative_test_subprocess() -> int:
    """
    Launch a subprocess that runs a deliberately wrong assertion
    (expects 'ok' for a timeout fixture). Returns the subprocess exit code,
    which must be non-zero.
    """
    negative_script = r"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from r02_t051_internal import _run_negative_assertion
sys.exit(_run_negative_assertion())
"""
    # We embed the negative assertion inline rather than a separate file,
    # by calling this module with a hidden flag.
    this_file = os.path.abspath(__file__)
    result = subprocess.run(
        [sys.executable, this_file, "--_negative_assertion"],
        capture_output=True,
        text=True,
    )
    return result.returncode


def _negative_assertion_main() -> int:
    """
    Deliberately wrong assertion: expects the timeout fixture to be classified
    as 'ok'. This MUST fail and return 1.
    """
    fix = _load_fixture("fixture_timeout.json")
    steps = fix["steps"]
    fetch_fn = _make_fixture_fetch(steps)
    fake_entry = {
        "name": "NegativeTest", "url": steps[0]["url"],
        "description": "deliberate failure", "auth": "No",
        "https": "Yes", "cors": "Unknown", "line_number": 999,
    }
    result = check_entry(fake_entry, fetch_fn)
    actual = result["classification"]
    expected_wrong = "ok"  # deliberately wrong expectation
    if actual == expected_wrong:
        print(f"Negative test unexpectedly passed: got '{actual}'")
        return 0
    else:
        print(
            f"Negative test correctly failed: "
            f"expected '{expected_wrong}', got '{actual}' — exit non-zero"
        )
        return 1  # non-zero exit proves assertion machinery works


# ---------------------------------------------------------------------------
# Live check mode
# ---------------------------------------------------------------------------

def run_live(readme_path: str) -> int:
    """
    Parse README, check the three entries over the network, write report.json.
    Returns 0 on success (even if entries have issues — only removal is blocked).
    """
    print(f"Parsing README: {readme_path}")
    entries = parse_readme(readme_path)
    if not entries:
        print("ERROR: No target entries found in README.", file=sys.stderr)
        return 1

    print(f"Found {len(entries)} target entries. Running live checks (sequential)…\n")
    request_counter = [0]
    results = []
    obs_date = datetime.now(timezone.utc).isoformat()

    for entry in entries:
        print(f"  Checking: {entry['name']}  ({entry['url'][:60]}…)")
        result = check_entry(entry, real_fetch, request_counter)
        results.append(result)
        _print_result_row(result)

    print(f"\nTotal requests made: {request_counter[0]}")

    # Write report
    os.makedirs(WORK_DIR, exist_ok=True)
    report = {
        "task": TASK_ID,
        "observation_date": obs_date,
        "readme_path": readme_path,
        "total_requests": request_counter[0],
        "results": results,
        "readme_unchanged": True,
        "readme_change_rationale": (
            "No changes made. Classification results do not meet the evidence bar "
            "for a catalogue correction (single-run automated check only)."
        ),
    }
    with open(REPORT_PATH, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    print(f"\nReport written to: {REPORT_PATH}")
    return 0


def _print_result_row(result: Dict) -> None:
    name = result["entry_name"]
    cls = result["classification"]
    rec = result["recommendation"]
    hops = result["hop_count"]
    final = result.get("final_url") or "-"
    utm = " [utm_flagged]" if result.get("utm_flagged") else ""
    err = f" ({result['error_kind']}: {result['error_detail']})" \
          if result.get("error_kind") else ""
    print(f"    {name:<25}  cls={cls}  hops={hops}  rec={rec}{utm}{err}")
    if final != result["entry_url"] and final != "-":
        print(f"    {'':25}  final_url={final}")


# ---------------------------------------------------------------------------
# Default mode — just print parsed entries
# ---------------------------------------------------------------------------

def run_default(readme_path: str) -> int:
    entries = parse_readme(readme_path)
    if not entries:
        print("No target entries found.", file=sys.stderr)
        return 1
    print(f"Parsed {len(entries)} entries from {readme_path}:\n")
    for e in entries:
        print(f"  L{e['line_number']:04d}  {e['name']}")
        print(f"         URL:  {e['url']}")
        print(f"         Auth={e['auth']}  HTTPS={e['https']}  CORS={e['cors']}")
        print(f"         Desc: {e['description'][:80]}")
        print()
    return 0


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="R02-T051: Verify redirects for Currency Exchange entries in README.md"
    )
    parser.add_argument(
        "--self-test", action="store_true",
        help="Run offline fixture-based tests and exit non-zero on failure.",
    )
    parser.add_argument(
        "--live", action="store_true",
        help="Fetch the three entries over the network and write work/R02-T051/report.json.",
    )
    parser.add_argument(
        "--readme", default=README_DEFAULT, metavar="PATH",
        help="Path to README.md (default: auto-detected from repo root).",
    )
    # Hidden flag for the negative-test subprocess (Amendment 8)
    parser.add_argument("--_negative_assertion", action="store_true",
                        help=argparse.SUPPRESS)
    args = parser.parse_args()

    if args._negative_assertion:
        sys.exit(_negative_assertion_main())

    if args.self_test:
        sys.exit(run_self_test(verbose=True))

    if args.live:
        sys.exit(run_live(args.readme))

    sys.exit(run_default(args.readme))


if __name__ == "__main__":
    main()
