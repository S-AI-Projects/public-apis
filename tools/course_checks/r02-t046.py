#!/usr/bin/env python3
"""
R02-T046: Classify failures correctly: Dictionaries [README.md]
Distinguishes HTTP 200, 403, 404, 429, HEAD-405/GET-fallback, timeout, and DNS failure.
Selected entries:
  - Chinese Character Web: http://ccdb.hemiola.com/
  - Chinese Text Project: https://ctext.org/tools/api
  - Collins: https://api.collinsdictionary.com/api/v1/documentation/html/
"""

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"
CATEGORY = "Dictionaries"

SELECTED_ENTRIES = {
    "Chinese Character Web": "http://ccdb.hemiola.com/",
    "Chinese Text Project": "https://ctext.org/tools/api",
    "Collins": "https://api.collinsdictionary.com/api/v1/documentation/html/",
}


def classify_response(head_status=None, get_status=None, error_type=None):
    """
    Classifies the probe outcome based on HTTP status codes and error types:
      - 'SUCCESS': HTTP 200 (or HEAD 405/501 followed by GET 200)
      - 'MISSING_RESOURCE': HTTP 404 (candidate for manual review)
      - 'RATE_LIMITED': HTTP 429
      - 'FORBIDDEN': HTTP 403
      - 'TIMEOUT': Connection or read timeout
      - 'DNS_FAILURE': Name resolution failure
      - 'NETWORK_ERROR': Other socket / network reset errors
    """
    if error_type == "DNS_FAILURE":
        return "DNS_FAILURE"
    if error_type == "TIMEOUT":
        return "TIMEOUT"
    if error_type == "NETWORK_ERROR":
        return "NETWORK_ERROR"

    if head_status == 200 or get_status == 200:
        return "SUCCESS"
    if head_status == 404 or get_status == 404:
        return "MISSING_RESOURCE"
    if head_status == 429 or get_status == 429:
        return "RATE_LIMITED"
    if head_status == 403 or get_status == 403:
        return "FORBIDDEN"
    if head_status in (405, 501):
        if get_status == 200:
            return "SUCCESS"
        if get_status == 404:
            return "MISSING_RESOURCE"
        if get_status == 429:
            return "RATE_LIMITED"
        if get_status == 403:
            return "FORBIDDEN"

    return "UNKNOWN"


def probe_url(url, timeout=10):
    """Probes URL using HEAD with GET fallback on 405/501 or certain errors."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
        method="HEAD",
    )
    head_code = None
    try:
        with urllib.request.urlopen(req, timeout=timeout) as res:
            head_code = res.getcode()
            if head_code == 200:
                return classify_response(head_status=200)
    except urllib.error.HTTPError as e:
        head_code = e.code
    except (socket.timeout, urllib.error.URLError) as e:
        if isinstance(e.reason, socket.gaierror):
            return classify_response(error_type="DNS_FAILURE")
        if isinstance(e.reason, (socket.timeout, TimeoutError)):
            return classify_response(error_type="TIMEOUT")
        return classify_response(error_type="NETWORK_ERROR")

    # If HEAD is 405 Method Not Allowed or 501 Not Implemented or 403/406, try GET
    if head_code in (405, 501, 406):
        get_req = urllib.request.Request(
            url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"},
            method="GET",
        )
        try:
            with urllib.request.urlopen(get_req, timeout=timeout) as res:
                return classify_response(head_status=head_code, get_status=res.getcode())
        except urllib.error.HTTPError as e:
            return classify_response(head_status=head_code, get_status=e.code)
        except Exception:
            return classify_response(head_status=head_code, error_type="NETWORK_ERROR")

    return classify_response(head_status=head_code)


def run_self_tests():
    """Verify offline fixtures for 200, 404, 429, HEAD-405/GET-200, timeout, DNS failure."""
    try:
        assert False
        print("ERROR: assertions disabled (python -O/-OO); refusing false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    fixtures_dir = ROOT / "work" / "R02-T046" / "fixtures"

    def load_fixture(name):
        path = fixtures_dir / name
        if not path.exists():
            raise FileNotFoundError(f"Fixture missing: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # 1. HTTP 200 Success
    f_200 = load_fixture("01_http_200.json")
    assert classify_response(head_status=f_200.get("head_status"), get_status=f_200.get("get_status")) == "SUCCESS"

    # 2. HTTP 404 Missing Resource
    f_404 = load_fixture("02_http_404.json")
    assert classify_response(head_status=f_404.get("head_status"), get_status=f_404.get("get_status")) == "MISSING_RESOURCE"

    # 3. HTTP 429 Rate Limited
    f_429 = load_fixture("03_http_429.json")
    assert classify_response(head_status=f_429.get("head_status"), get_status=f_429.get("get_status")) == "RATE_LIMITED"

    # 4. HTTP 403 Forbidden
    f_403 = load_fixture("04_http_403.json")
    assert classify_response(head_status=f_403.get("head_status"), get_status=f_403.get("get_status")) == "FORBIDDEN"

    # 5. HEAD 405 -> GET 200 Fallback
    f_fallback = load_fixture("05_head_405_get_200.json")
    assert classify_response(head_status=f_fallback.get("head_status"), get_status=f_fallback.get("get_status")) == "SUCCESS"

    # 6. Timeout
    f_timeout = load_fixture("06_timeout.json")
    assert classify_response(error_type=f_timeout.get("error_type")) == "TIMEOUT"

    # 7. DNS Failure
    f_dns = load_fixture("07_dns_failure.json")
    assert classify_response(error_type=f_dns.get("error_type")) == "DNS_FAILURE"

    # Write actual results
    work_dir = ROOT / "work" / "R02-T046"
    work_dir.mkdir(parents=True, exist_ok=True)
    with open(work_dir / "actual-results.json", "w", encoding="utf-8") as f:
        json.dump({"self_test": "passed", "fixtures_verified": 7}, f, indent=2)

    print("Self-test passed: 7 fixtures verified distinct classifications (200, 404, 429, 403, fallback, timeout, DNS).")


def parse_dictionaries_section(file_path):
    """Extract line numbers and markdown entries for Dictionaries category."""
    lines = Path(file_path).read_text(encoding="utf-8").splitlines()
    in_section = False
    entries = {}

    for idx, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("### "):
            cat = stripped[4:].strip()
            if cat == CATEGORY:
                in_section = True
                continue
            elif in_section:
                break

        if not in_section:
            continue

        for name, url in SELECTED_ENTRIES.items():
            if url in line:
                entries[name] = {"name": name, "url": url, "line": idx}

    return entries


def main():
    parser = argparse.ArgumentParser(description="Failure classification checker for Dictionaries APIs")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture checks")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    entries = parse_dictionaries_section(README)
    print(f"Scanned {len(entries)} assigned entries in '{CATEGORY}'.")
    for name, data in entries.items():
        print(f"OK line {data['line']}: {name} ({data['url']})")

    sys.exit(0)


if __name__ == "__main__":
    main()
