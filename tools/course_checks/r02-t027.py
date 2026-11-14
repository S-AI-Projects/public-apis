#!/usr/bin/env python3
"""Failure classification and metadata verification checker for assigned Machine Learning APIs in public-apis."""

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES_DIR = ROOT / "tools/course_checks/fixtures/r02-t027"

CATEGORY = "Machine Learning"
SELECTED_APIS = ["AI Economics Tools", "AI For Thai", "AI Stupid Level"]

DEFAULT_TIMEOUT = 5.0

# Allowed metadata values per CONTRIBUTING.md
VALID_AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}

# Authoritative verified metadata
VERIFIED_METADATA = {
    "AI Economics Tools": {
        "url": "https://piszczek.pl/tools/api",
        "description": "Token cost, LLM energy, agent-hour and Proof-Adjusted Autonomy calculators by Michał Piszczek",
        "auth": "No",
        "https": "Yes",
        "cors": "Yes",
        "category": "Machine Learning",
    },
    "AI For Thai": {
        "url": "https://aiforthai.in.th/index.php",
        "description": "Free Various Thai AI API",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "Yes",
        "category": "Machine Learning",
    },
    "AI Stupid Level": {
        "url": "https://aistupidlevel.info/api-docs",
        "description": "Benchmark scores, rankings and drift data for major LLM APIs, re-measured on a fixed schedule",
        "auth": "apiKey",
        "https": "Yes",
        "cors": "No",
        "category": "Machine Learning",
    },
}

# Set of API names manually confirmed as permanently missing/defunct
# An automated failure (including 404) will NOT trigger removal recommendation unless present here.
MANUALLY_CONFIRMED_MISSING: set[str] = set()


# ---------------------------------------------------------------------------
# Failure Classification & Request Helpers
# ---------------------------------------------------------------------------

class MockHttpResponse:
    """Mock HTTP response supporting context manager and explicit close for resource safety."""
    def __init__(self, status: int = 200, reason: str = "OK"):
        self.status = status
        self.code = status
        self.reason = reason
        self.closed = False

    def read(self, *args, **kwargs) -> bytes:
        return b""

    def close(self) -> None:
        self.closed = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False


def classify_http_status(status_code: int) -> str:
    """Classify an HTTP response status code into required labels."""
    if status_code == 200:
        return "success"
    elif status_code == 404:
        return "missing_resource"
    elif status_code == 403:
        return "forbidden"
    elif status_code == 429:
        return "rate_limited"
    else:
        return f"http_{status_code}"


def classify_exception(exc: Exception) -> tuple[int | None, str]:
    """Classify a network or HTTP exception into HTTP status code and classification label."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code, classify_http_status(exc.code)

    if isinstance(exc, (socket.timeout, TimeoutError)):
        return None, "timeout"

    if isinstance(exc, urllib.error.URLError):
        reason = exc.reason
        if isinstance(reason, (socket.timeout, TimeoutError)) or "timed out" in str(reason).lower():
            return None, "timeout"
        if isinstance(reason, socket.gaierror) or any(
            pattern in str(reason).lower()
            for pattern in ["nodename nor servname", "name or service not known", "getaddrinfo failed"]
        ):
            return None, "dns_failure"
        return None, f"url_error_{type(reason).__name__}"

    if isinstance(exc, socket.gaierror):
        return None, "dns_failure"

    return None, f"error_{type(exc).__name__}"


def evaluate_removal(
    classification: str,
    manually_confirmed_missing: bool = False,
) -> tuple[bool, str]:
    """
    Determine if catalogue removal should be recommended.

    Policy:
    - Automated failures (including 404 missing_resource) do NOT automatically trigger removal.
    - Only recommend removal when the resource is manually confirmed missing.
    - Unconfirmed missing resources are retained for manual review.
    """
    if classification == "missing_resource":
        if manually_confirmed_missing:
            return True, "Resource manually confirmed missing; removal recommended."
        else:
            return False, "Unconfirmed missing resource: single automated 404 failure; manual confirmation required before removal."
    elif classification == "success":
        return False, "Resource active and accessible; keep entry."
    else:
        return False, f"Automated failure ({classification}) does not prove resource is dead; keep entry for manual review."


def probe_url(
    url: str,
    timeout: float = DEFAULT_TIMEOUT,
    opener=None,
    manually_confirmed_missing: bool = False,
) -> dict:
    """
    Sequentially probe a URL using HEAD with fallback to GET on 405/501.
    Classify failure according to course specifications and safely close responses.
    """
    if opener is None:
        opener = urllib.request.urlopen

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) public-apis-checker/1.0",
        "Accept": "*/*",
    }

    method_used = "HEAD"
    http_status = None
    classification = None
    retried_with_get = False
    details = ""

    # 1. Attempt HEAD request
    try:
        req = urllib.request.Request(url, headers=headers, method="HEAD")
        resp = opener(req, timeout=timeout)
        try:
            http_status = getattr(resp, "status", getattr(resp, "code", 200))
            classification = classify_http_status(http_status)
        finally:
            if hasattr(resp, "close") and callable(resp.close):
                resp.close()
    except urllib.error.HTTPError as head_err:
        http_status = head_err.code
        if hasattr(head_err, "close") and callable(head_err.close):
            try:
                head_err.close()
            except Exception:
                pass
        if head_err.code in (405, 501):
            # HEAD not allowed or not implemented; retry using GET
            retried_with_get = True
            method_used = "GET"
            try:
                get_req = urllib.request.Request(url, headers=headers, method="GET")
                get_resp = opener(get_req, timeout=timeout)
                try:
                    http_status = getattr(get_resp, "status", getattr(get_resp, "code", 200))
                    classification = classify_http_status(http_status)
                    details = f"HEAD returned {head_err.code}; retried with GET and received {http_status}"
                finally:
                    if hasattr(get_resp, "close") and callable(get_resp.close):
                        get_resp.close()
            except Exception as get_err:
                http_status, classification = classify_exception(get_err)
                details = f"HEAD returned {head_err.code}; GET retry failed with {classification}"
                if hasattr(get_err, "close") and callable(get_err.close):
                    try:
                        get_err.close()
                    except Exception:
                        pass
        else:
            classification = classify_http_status(head_err.code)
    except Exception as exc:
        http_status, classification = classify_exception(exc)
        if hasattr(exc, "close") and callable(exc.close):
            try:
                exc.close()
            except Exception:
                pass

    removal_rec, rec_reason = evaluate_removal(
        classification=classification,
        manually_confirmed_missing=manually_confirmed_missing,
    )

    return {
        "http_status": http_status,
        "method_used": method_used,
        "failure_classification": classification,
        "retried_with_get": retried_with_get,
        "details": details,
        "manually_confirmed_missing": manually_confirmed_missing,
        "removal_recommended": removal_rec,
        "recommendation_reason": rec_reason,
    }


# ---------------------------------------------------------------------------
# Table & Markdown Parsing
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
    Extract (name, url) from Markdown link format [Name](URL).
    Supports URLs with balanced parentheses and preserves exact URL text.
    """
    stripped = cell.strip()
    if not stripped.startswith("["):
        return None

    idx = -1
    for i in range(1, len(stripped) - 1):
        if stripped[i:i+2] == "](" and (i == 0 or stripped[i-1] != "\\"):
            idx = i
            break

    if idx == -1:
        return None

    name = stripped[1:idx].strip()
    if not name:
        return None

    url_part = stripped[idx + 2:]
    if not url_part.endswith(")"):
        return None

    url_content = url_part[:-1]

    depth = 0
    for char in url_content:
        if char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth < 0:
                return None
    if depth != 0:
        return None

    return name, url_content


def check_duplicate_and_missing_entries(entries: list[dict]) -> tuple[list[str], list[str], list[dict]]:
    """Verify that each selected API appears exactly once."""
    counts = {name: 0 for name in SELECTED_APIS}
    for e in entries:
        name = e["name"]
        if name in counts:
            counts[name] += 1

    duplicate_names = [name for name in SELECTED_APIS if counts[name] > 1]
    missing_names = [name for name in SELECTED_APIS if counts[name] == 0]

    errors = []
    for name in duplicate_names:
        errors.append({
            "name": name,
            "category": CATEGORY,
            "error": f"Duplicate entry detected: '{name}' appears {counts[name]} times in category '{CATEGORY}' (expected exactly once)",
        })
    for name in missing_names:
        errors.append({
            "name": name,
            "category": CATEGORY,
            "error": f"Missing required entry: '{name}' was not found in category '{CATEGORY}'",
        })

    return duplicate_names, missing_names, errors


def parse_machine_learning_entries(markdown_text: str) -> tuple[list[dict], list[dict]]:
    """Parse Machine Learning category entries from markdown, preserving line numbers and capturing errors."""
    lines = markdown_text.splitlines()
    in_section = False
    inside_code_block = False
    parsed_entries: list[dict] = []
    errors: list[dict] = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("```") or stripped.startswith("~~~"):
            inside_code_block = not inside_code_block
            continue
        if inside_code_block:
            continue

        heading_match = re.match(r"^###\s+(.+?)\s*$", line)
        if heading_match:
            heading_title = heading_match.group(1).strip()
            if in_section:
                break
            if heading_title == CATEGORY:
                in_section = True
            continue

        if not in_section:
            continue

        if stripped.startswith("**[⬆ Back to Index"):
            break

        if not stripped.startswith("|"):
            for sel_name in SELECTED_APIS:
                if sel_name in stripped:
                    errors.append({
                        "name": sel_name,
                        "line": line_number,
                        "category": CATEGORY,
                        "error": "Malformed row: table row does not start with pipe '|'",
                        "raw_line": line,
                    })
            continue

        if stripped.startswith("|:---") or stripped.startswith("|---"):
            continue

        raw_cells = split_markdown_row(line)
        if len(raw_cells) == 0:
            continue

        if raw_cells[0].lower() == "api" and len(raw_cells) >= 2 and raw_cells[1].lower() == "description":
            continue

        link_info = extract_markdown_link(raw_cells[0])
        if not link_info:
            for sel_name in SELECTED_APIS:
                if sel_name in raw_cells[0]:
                    errors.append({
                        "name": sel_name,
                        "line": line_number,
                        "category": CATEGORY,
                        "error": f"Malformed row: API name cell '{raw_cells[0]}' is not a valid markdown link [Name](URL)",
                        "raw_line": line,
                    })
            continue

        name, url = link_info

        if name not in SELECTED_APIS:
            continue

        actual_cols = len(raw_cells)
        if actual_cols != 5:
            if actual_cols < 5:
                err_msg = f"Missing required table column(s): expected exactly 5 columns, found {actual_cols}"
            else:
                err_msg = f"Extra table column(s) detected: expected exactly 5 columns, found {actual_cols}"
            errors.append({
                "name": name,
                "url": url,
                "line": line_number,
                "category": CATEGORY,
                "actual_column_count": actual_cols,
                "error": err_msg,
                "raw_line": line,
            })
            continue

        if any(raw_cells[i] == "" for i in range(5)):
            errors.append({
                "name": name,
                "url": url,
                "line": line_number,
                "category": CATEGORY,
                "actual_column_count": actual_cols,
                "error": "Empty required table column encountered in row",
                "raw_line": line,
            })
            continue

        description = raw_cells[1]
        auth = raw_cells[2].strip("`").strip()
        https = raw_cells[3]
        cors = raw_cells[4]

        parsed_entries.append({
            "name": name,
            "url": url,
            "description": description,
            "auth": auth,
            "https": https,
            "cors": cors,
            "category": CATEGORY,
            "line": line_number,
        })

    return parsed_entries, errors


def validate_metadata(entry: dict) -> dict:
    """Validate entry metadata against vocabulary and verified reference values."""
    issues = []
    name = entry["name"]

    if entry["auth"] not in VALID_AUTH:
        issues.append(f"Invalid Auth value: '{entry['auth']}' (allowed: {sorted(VALID_AUTH)})")
    if entry["https"] not in VALID_HTTPS:
        issues.append(f"Invalid HTTPS value: '{entry['https']}' (allowed: {sorted(VALID_HTTPS)})")
    if entry["cors"] not in VALID_CORS:
        issues.append(f"Invalid CORS value: '{entry['cors']}' (allowed: {sorted(VALID_CORS)})")

    if name in VERIFIED_METADATA:
        expected = VERIFIED_METADATA[name]
        if entry["url"] != expected["url"]:
            issues.append(f"URL mismatch: expected '{expected['url']}', found '{entry['url']}'")
        if entry["description"] != expected["description"]:
            issues.append(f"Description mismatch: expected '{expected['description']}', found '{entry['description']}'")
        if entry["auth"] != expected["auth"]:
            issues.append(f"Auth mismatch: expected '{expected['auth']}', found '{entry['auth']}'")
        if entry["https"] != expected["https"]:
            issues.append(f"HTTPS mismatch: expected '{expected['https']}', found '{entry['https']}'")
        if entry["cors"] != expected["cors"]:
            issues.append(f"CORS mismatch: expected '{expected['cors']}', found '{entry['cors']}'")
    else:
        issues.append(f"Entry '{name}' is not in the assigned selected APIs list")

    return {
        "status": "valid" if not issues else "invalid",
        "issues": issues,
    }


# ---------------------------------------------------------------------------
# Self-Tests (Offline & Fixture-Driven)
# ---------------------------------------------------------------------------

def assert_result_matches_expected(result: dict, expected: dict, context: str = "") -> None:
    """Compare all expected fields against the actual probe result dict."""
    for key, expected_value in expected.items():
        assert key in result, f"[{context}] Missing key '{key}' in probe result: {result}"
        actual_value = result[key]
        assert actual_value == expected_value, (
            f"[{context}] Field '{key}' mismatch: expected {expected_value!r}, got {actual_value!r}"
        )


def run_self_tests() -> None:
    """Execute deterministic offline regression tests against fixtures and mock scenarios."""
    print("Running self-tests for R02-T027 (Classify Failures Correctly — Machine Learning)...")

    # 1. Test HTTP 200 fixture (fixture-driven)
    http_200_f = FIXTURES_DIR / "http_200.json"
    assert http_200_f.exists(), f"Missing fixture: {http_200_f}"
    http_200_cfg = json.loads(http_200_f.read_text(encoding="utf-8"))
    mock_200 = MockHttpResponse(
        status=http_200_cfg["response"]["status"],
        reason=http_200_cfg["response"].get("reason", "OK"),
    )
    def opener_200(req, timeout=5.0):
        return mock_200
    res_200 = probe_url("https://example.com/api", opener=opener_200)
    assert_result_matches_expected(res_200, http_200_cfg["expected"], context="http_200")
    assert mock_200.closed is True, "Mock response for HTTP 200 was not closed"

    # 2. Test HTTP 404 fixture (fixture-driven)
    http_404_f = FIXTURES_DIR / "http_404.json"
    assert http_404_f.exists(), f"Missing fixture: {http_404_f}"
    http_404_cfg = json.loads(http_404_f.read_text(encoding="utf-8"))
    def opener_404(req, timeout=5.0):
        raise urllib.error.HTTPError(
            req.full_url,
            http_404_cfg["http_error"]["code"],
            http_404_cfg["http_error"].get("msg", "Not Found"),
            {},
            None,
        )
    res_404 = probe_url("https://example.com/api", opener=opener_404)
    assert_result_matches_expected(res_404, http_404_cfg["expected"], context="http_404")

    # 3. Test HTTP 403 fixture (fixture-driven)
    http_403_f = FIXTURES_DIR / "http_403.json"
    assert http_403_f.exists(), f"Missing fixture: {http_403_f}"
    http_403_cfg = json.loads(http_403_f.read_text(encoding="utf-8"))
    def opener_403(req, timeout=5.0):
        raise urllib.error.HTTPError(
            req.full_url,
            http_403_cfg["http_error"]["code"],
            http_403_cfg["http_error"].get("msg", "Forbidden"),
            {},
            None,
        )
    res_403 = probe_url("https://example.com/api", opener=opener_403)
    assert_result_matches_expected(res_403, http_403_cfg["expected"], context="http_403")

    # 4. Test HTTP 429 fixture (fixture-driven)
    http_429_f = FIXTURES_DIR / "http_429.json"
    assert http_429_f.exists(), f"Missing fixture: {http_429_f}"
    http_429_cfg = json.loads(http_429_f.read_text(encoding="utf-8"))
    def opener_429(req, timeout=5.0):
        raise urllib.error.HTTPError(
            req.full_url,
            http_429_cfg["http_error"]["code"],
            http_429_cfg["http_error"].get("msg", "Too Many Requests"),
            {},
            None,
        )
    res_429 = probe_url("https://example.com/api", opener=opener_429)
    assert_result_matches_expected(res_429, http_429_cfg["expected"], context="http_429")

    # 5. Test HEAD 405 followed by GET 200 fixture (fixture-driven)
    head_405_f = FIXTURES_DIR / "head_405_get_200.json"
    assert head_405_f.exists(), f"Missing fixture: {head_405_f}"
    head_405_cfg = json.loads(head_405_f.read_text(encoding="utf-8"))
    get_mock = MockHttpResponse(
        status=head_405_cfg["get_response"]["status"],
        reason=head_405_cfg["get_response"].get("reason", "OK"),
    )
    def opener_head_405_get_200(req, timeout=5.0):
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError(
                req.full_url,
                head_405_cfg["head_error"]["code"],
                head_405_cfg["head_error"].get("msg", "Method Not Allowed"),
                {},
                None,
            )
        return get_mock
    res_head_405 = probe_url("https://example.com/api", opener=opener_head_405_get_200)
    assert_result_matches_expected(res_head_405, head_405_cfg["expected"], context="head_405_get_200")
    assert get_mock.closed is True, "GET fallback mock response was not closed"

    # Also test HEAD 501 fallback to GET 200
    mock_501_get = MockHttpResponse(200)
    def opener_head_501_get_200(req, timeout=5.0):
        if req.get_method() == "HEAD":
            raise urllib.error.HTTPError(req.full_url, 501, "Not Implemented", {}, None)
        return mock_501_get
    res_head_501 = probe_url("https://example.com/api", opener=opener_head_501_get_200)
    assert res_head_501["http_status"] == 200
    assert res_head_501["method_used"] == "GET"
    assert res_head_501["failure_classification"] == "success"
    assert mock_501_get.closed is True

    # 6. Test Timeout fixture (fixture-driven)
    timeout_f = FIXTURES_DIR / "timeout.json"
    assert timeout_f.exists(), f"Missing fixture: {timeout_f}"
    timeout_cfg = json.loads(timeout_f.read_text(encoding="utf-8"))
    def opener_timeout(req, timeout=5.0):
        raise urllib.error.URLError(socket.timeout(timeout_cfg.get("reason_msg", "timed out")))
    res_timeout = probe_url("https://example.com/api", opener=opener_timeout)
    assert_result_matches_expected(res_timeout, timeout_cfg["expected"], context="timeout")

    # 7. Test DNS failure fixture (fixture-driven)
    dns_f = FIXTURES_DIR / "dns_failure.json"
    assert dns_f.exists(), f"Missing fixture: {dns_f}"
    dns_cfg = json.loads(dns_f.read_text(encoding="utf-8"))
    def opener_dns(req, timeout=5.0):
        raise urllib.error.URLError(socket.gaierror(8, dns_cfg.get("reason_msg", "nodename nor servname provided")))
    res_dns = probe_url("https://example.com/api", opener=opener_dns)
    assert_result_matches_expected(res_dns, dns_cfg["expected"], context="dns_failure")

    # 8. Test Other HTTP errors fixture (fixture-driven for 500, 502, 503, 401)
    other_f = FIXTURES_DIR / "other_http_errors.json"
    assert other_f.exists(), f"Missing fixture: {other_f}"
    other_cfg = json.loads(other_f.read_text(encoding="utf-8"))
    for idx, tc in enumerate(other_cfg["test_cases"]):
        def opener_err(req, timeout=5.0, code=tc["code"], msg=tc["msg"]):
            raise urllib.error.HTTPError(req.full_url, code, msg, {}, None)
        res_other = probe_url("https://example.com/api", opener=opener_err)
        assert_result_matches_expected(res_other, tc["expected"], context=f"other_http_errors_{tc['code']}")

    # 9. Test Manually confirmed missing resource fixture (fixture-driven)
    man_f = FIXTURES_DIR / "manually_confirmed_missing.json"
    assert man_f.exists(), f"Missing fixture: {man_f}"
    man_cfg = json.loads(man_f.read_text(encoding="utf-8"))
    def opener_man(req, timeout=5.0):
        raise urllib.error.HTTPError(
            req.full_url,
            man_cfg["http_error"]["code"],
            man_cfg["http_error"].get("msg", "Not Found"),
            {},
            None,
        )
    res_man = probe_url("https://example.com/api", opener=opener_man, manually_confirmed_missing=man_cfg["manually_confirmed"])
    assert_result_matches_expected(res_man, man_cfg["expected"], context="manually_confirmed_missing")

    # 10. Test Unconfirmed missing resource fixture (fixture-driven)
    unconf_f = FIXTURES_DIR / "unconfirmed_missing.json"
    assert unconf_f.exists(), f"Missing fixture: {unconf_f}"
    unconf_cfg = json.loads(unconf_f.read_text(encoding="utf-8"))
    def opener_unconf(req, timeout=5.0):
        raise urllib.error.HTTPError(
            req.full_url,
            unconf_cfg["http_error"]["code"],
            unconf_cfg["http_error"].get("msg", "Not Found"),
            {},
            None,
        )
    res_unconf = probe_url("https://example.com/api", opener=opener_unconf, manually_confirmed_missing=unconf_cfg["manually_confirmed"])
    assert_result_matches_expected(res_unconf, unconf_cfg["expected"], context="unconfirmed_missing")

    # 11. Negative self-test check: confirm that a deliberately incorrect expected classification causes a failing assertion
    deliberately_wrong = {"failure_classification": "deliberately_incorrect_label"}
    assertion_failed = False
    try:
        assert_result_matches_expected(res_200, deliberately_wrong, context="negative_test_check")
    except AssertionError:
        assertion_failed = True
    assert assertion_failed is True, "Negative self-test failed: assertion did not raise on deliberate classification mismatch!"

    # 12. Test Correct source line tracking fixture
    line_f = FIXTURES_DIR / "line_tracking.md"
    assert line_f.exists(), f"Missing fixture: {line_f}"
    line_entries, line_errs = parse_machine_learning_entries(line_f.read_text(encoding="utf-8"))
    assert len(line_errs) == 0
    assert len(line_entries) == 3
    assert [e["line"] for e in line_entries] == [13, 14, 15]

    # 13. Test Selected entries outside category ignored fixture
    outside_f = FIXTURES_DIR / "outside_category.md"
    assert outside_f.exists(), f"Missing fixture: {outside_f}"
    outside_entries, outside_errs = parse_machine_learning_entries(outside_f.read_text(encoding="utf-8"))
    assert len(outside_errs) == 0
    assert len(outside_entries) == 0, f"Expected 0 entries from outside category, got {len(outside_entries)}"

    # 14. Test valid entries markdown fixture
    valid_f = FIXTURES_DIR / "valid_entries.md"
    assert valid_f.exists(), f"Missing fixture: {valid_f}"
    v_entries, v_errs = parse_machine_learning_entries(valid_f.read_text(encoding="utf-8"))
    assert len(v_errs) == 0
    assert len(v_entries) == 3
    for ve in v_entries:
        vm = validate_metadata(ve)
        assert vm["status"] == "valid", f"Metadata error: {vm}"

    # 15. Test Root README.md parsing & lines
    assert README.exists(), f"Missing README.md at {README}"
    readme_entries, readme_errs = parse_machine_learning_entries(README.read_text(encoding="utf-8"))
    assert len(readme_errs) == 0, f"Parse errors in README.md: {readme_errs}"
    assert len(readme_entries) == 3, f"Expected 3 entries in README.md, got {len(readme_entries)}"

    readme_by_name = {e["name"]: e for e in readme_entries}
    assert "AI Economics Tools" in readme_by_name
    assert "AI For Thai" in readme_by_name
    assert "AI Stupid Level" in readme_by_name

    assert readme_by_name["AI Economics Tools"]["line"] == 1747
    assert readme_by_name["AI For Thai"]["line"] == 1748
    assert readme_by_name["AI Stupid Level"]["line"] == 1749

    for re_entry in readme_entries:
        vm = validate_metadata(re_entry)
        assert vm["status"] == "valid", f"Metadata validation issue for {re_entry['name']}: {vm['issues']}"

    print("All offline tests passed!")


# ---------------------------------------------------------------------------
# Main Execution
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run deterministic offline self-tests against fixtures and mocked scenarios",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT,
        help=f"Timeout in seconds for live network requests (default: {DEFAULT_TIMEOUT}s)",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    readme_text = README.read_text(encoding="utf-8")
    entries, parse_errors = parse_machine_learning_entries(readme_text)

    duplicate_names, missing_names, cardinality_errors = check_duplicate_and_missing_entries(entries)
    all_errors = parse_errors + cardinality_errors

    reports = []
    # Sequential probing of the three fixed URLs with low concurrency
    for entry in entries:
        meta_val = validate_metadata(entry)
        is_manually_confirmed = entry["name"] in MANUALLY_CONFIRMED_MISSING
        net_result = probe_url(
            entry["url"],
            timeout=args.timeout,
            manually_confirmed_missing=is_manually_confirmed,
        )

        entry_report = {
            "name": entry["name"],
            "url": entry["url"],
            "description": entry["description"],
            "auth": entry["auth"],
            "https": entry["https"],
            "cors": entry["cors"],
            "category": entry["category"],
            "line": entry["line"],
            "http_status": net_result["http_status"],
            "method_used": net_result["method_used"],
            "failure_classification": net_result["failure_classification"],
            "retried_with_get": net_result["retried_with_get"],
            "manually_confirmed_missing": net_result["manually_confirmed_missing"],
            "removal_recommended": net_result["removal_recommended"],
            "recommendation_reason": net_result["recommendation_reason"],
            "status": meta_val["status"],
            "issues": meta_val["issues"],
        }
        reports.append(entry_report)

    summary = {
        "category": CATEGORY,
        "total_selected": len(SELECTED_APIS),
        "total_parsed": len(entries),
        "duplicate_entries": duplicate_names,
        "missing_entries": missing_names,
        "parse_errors": all_errors,
        "valid_count": sum(1 for r in reports if r["status"] == "valid"),
        "invalid_count": sum(1 for r in reports if r["status"] == "invalid"),
        "entries": reports,
    }

    print(json.dumps(summary, indent=2, ensure_ascii=False))

    # Save evidence artifacts to work/R02-T027/
    work_dir = ROOT / "work/R02-T027"
    work_dir.mkdir(parents=True, exist_ok=True)

    actual_file = work_dir / "actual.json"
    actual_file.write_text(json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    parsed_file = work_dir / "parsed-entries.json"
    parsed_file.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"\nReport saved to {actual_file.relative_to(ROOT)}")

    if (
        all_errors
        or duplicate_names
        or missing_names
        or len(entries) != len(SELECTED_APIS)
        or any(r["status"] == "invalid" for r in reports)
    ):
        sys.exit(1)


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc or type(exc).__name__}", file=sys.stderr)
        sys.exit(1)
