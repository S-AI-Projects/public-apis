#!/usr/bin/env python3
"""R02-T037 availability checker for three Games & Comics entries.

The checker parses only the assigned README table and probes only the three
selected APIs.  It is deliberately small and uses the standard library only.

Usage:
    python3 tools/course_checks/r02-t037.py
    python3 tools/course_checks/r02-t037.py --self-test
"""

from __future__ import annotations

import argparse
import json
import re
import socket
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CATEGORY = "Games & Comics"
SELECTED_NAMES = ("AmiiboAPI", "Animal Crossing: New Horizons", "Astroworld")
# Only these two HEAD statuses trigger the GET fallback.  A 403 or 404 from
# HEAD is meaningful and must not be retried as GET.
HEAD_UNSUPPORTED = frozenset({405, 501})

SUCCESS = "Success"
MISSING = "Missing resource (Not Found)"
RATE_LIMITED = "Rate Limited"
FORBIDDEN = "Forbidden"
TIMEOUT = "Timeout"
DNS_FAILURE = "DNS Failure"
SUCCESS_GET_FALLBACK = "Success via GET fallback"
HTTP_ERROR = "HTTP Error"
NETWORK_ERROR = "Network Error"

USER_AGENT = "public-apis-course-check/R02-T037 (+https://github.com/S-AI-Projects/public-apis)"

ROW_RE = re.compile(r"^\[([^\]]+)\]\(([^)]+)\)$")


@dataclass(frozen=True)
class Entry:
    name: str
    url: str
    line: int
    auth: str
    https: str
    cors: str


@dataclass(frozen=True)
class Outcome:
    classification: str
    method: str
    status: int | None
    detail: str
    final_url: str | None = None


def classify_status(status: int) -> str:
    if status == 200:
        return SUCCESS
    if status == 403:
        return FORBIDDEN
    if status == 404:
        return MISSING
    if status == 429:
        return RATE_LIMITED
    return HTTP_ERROR


def classify_error(error: BaseException) -> str:
    """Map a network exception to a distinct, non-generic classification."""
    if isinstance(error, urllib.error.URLError) and isinstance(error.reason, BaseException):
        return classify_error(error.reason)
    if isinstance(error, (socket.timeout, TimeoutError)):
        return TIMEOUT
    if isinstance(error, socket.gaierror):
        return DNS_FAILURE
    return NETWORK_ERROR


def parse_readme(text: str) -> tuple[str, dict[str, Entry]]:
    """Return the assigned category and selected entries with 1-based README lines."""
    lines = text.splitlines()
    heading = f"### {CATEGORY}"
    start = next((i for i, line in enumerate(lines) if line.strip() == heading), None)
    if start is None:
        raise ValueError(f"category heading not found: {heading}")

    entries: dict[str, Entry] = {}
    for index in range(start + 1, len(lines)):
        line = lines[index]
        if line.startswith("## ") or line.startswith("### "):
            break
        if not line.strip().startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5:
            continue
        match = ROW_RE.match(cells[0])
        if not match:
            continue
        name, url = match.groups()
        if name in SELECTED_NAMES:
            entries[name] = Entry(
                name=name,
                url=url,
                line=index + 1,
                auth=cells[2],
                https=cells[3],
                cors=cells[4],
            )

    missing = [name for name in SELECTED_NAMES if name not in entries]
    if missing:
        raise ValueError(f"selected entries not found in {heading}: {', '.join(missing)}")
    return CATEGORY, entries


def urllib_transport(url: str, method: str, timeout: float) -> tuple[int, str]:
    request = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, response.geturl()
    except urllib.error.HTTPError as error:
        try:
            return error.code, error.geturl()
        finally:
            error.close()


def attempt(url: str, method: str, timeout: float, transport: Callable) -> Outcome:
    try:
        status, final_url = transport(url, method, timeout)
    except Exception as error:  # noqa: BLE001 - classify every network failure explicitly
        classification = classify_error(error)
        return Outcome(classification, method, None, f"{type(error).__name__}: {error}")
    return Outcome(classify_status(status), method, status, f"HTTP {status}", final_url)


def probe(url: str, timeout: float, transport: Callable = urllib_transport) -> Outcome:
    """Probe HEAD first and retry with GET only when HEAD is unsupported."""
    head = attempt(url, "HEAD", timeout, transport)
    if head.status not in HEAD_UNSUPPORTED:
        return head

    get = attempt(url, "GET", timeout, transport)
    detail = f"HEAD returned {head.status}; GET {get.detail}"
    if get.status == 200:
        return Outcome(SUCCESS_GET_FALLBACK, "GET", 200, detail, get.final_url)
    return Outcome(get.classification, "GET", get.status, detail, get.final_url)


def run_checks(readme: Path, timeout: float) -> int:
    try:
        category, entries = parse_readme(readme.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2

    print("R02-T037 availability checker")
    print(f"README: {readme}")
    print(f"Category: {category}")
    print(f"Mode: live, sequential, timeout {timeout:g}s")
    print()

    counts: dict[str, int] = {}
    for index, name in enumerate(SELECTED_NAMES, start=1):
        entry = entries[name]
        print(f"[{index}/{len(SELECTED_NAMES)}] {entry.name}")
        print(f"  README line: {readme.name}:{entry.line}")
        print(f"  URL: {entry.url}")
        print(f"  Catalogue metadata: Auth={entry.auth}, HTTPS={entry.https}, CORS={entry.cors}")

        outcome = probe(entry.url, timeout)
        counts[outcome.classification] = counts.get(outcome.classification, 0) + 1
        print(f"  Request: {outcome.method} -> {outcome.detail}")
        print(f"  Result: {outcome.classification}")
        if outcome.final_url and outcome.final_url != entry.url:
            print(f"  Final URL: {outcome.final_url}")
        if outcome.classification == MISSING:
            print("  Action: HTTP 404 is not proof of removal; confirm the URL and service status manually.")
        elif outcome.classification in {TIMEOUT, DNS_FAILURE, NETWORK_ERROR}:
            print("  Action: temporary network failure; retry later and verify manually before any change.")
        elif outcome.classification in {FORBIDDEN, RATE_LIMITED}:
            print("  Action: access limitation, not evidence that the API is missing.")
        print()

    summary = ", ".join(f"{label}={count}" for label, count in sorted(counts.items()))
    print(f"Summary: {summary}")
    print("Removal policy: a single failed request is never sufficient evidence for removal.")
    print("Preserve entries unless a missing resource is manually confirmed with reliable evidence.")
    return 0


def fixture_transport(responses: dict) -> Callable:
    exceptions = {
        "timeout": socket.timeout("timed out"),
        "dns": socket.gaierror(socket.EAI_NONAME, "Name or service not known"),
    }

    def transport(url: str, method: str, timeout: float) -> tuple[int, str]:
        spec = responses.get(method)
        if spec is None:
            raise AssertionError(f"fixture has no simulated {method} response")
        if "exception" in spec:
            try:
                raise exceptions[spec["exception"]]
            except KeyError:
                raise AssertionError(f"unknown fixture exception: {spec['exception']}") from None
        return int(spec["status"]), url

    return transport


def check_fixture(path: Path) -> list[str]:
    """Run one JSON fixture and return human-readable assertion failures."""
    data = json.loads(path.read_text(encoding="utf-8"))
    expected = data["expected"]
    outcome = probe(
        data.get("url", "https://fixture.invalid/r02-t037"),
        float(data.get("timeout", 5)),
        fixture_transport(data["responses"]),
    )

    failures = []
    if outcome.classification != expected["classification"]:
        failures.append(f"classification: expected {expected['classification']!r}, got {outcome.classification!r}")
    if outcome.method != expected["method"]:
        failures.append(f"method: expected {expected['method']!r}, got {outcome.method!r}")
    if outcome.status != expected["status"]:
        failures.append(f"status: expected {expected['status']!r}, got {outcome.status!r}")
    for forbidden in data.get("must_not_be", []):
        if outcome.classification == forbidden:
            failures.append(f"negative assertion failed: classification must not be {forbidden!r}")

    print(f"fixture: {path.name}")
    print(f"  expected: {expected['classification']} / {expected['method']} / {expected['status']}")
    print(f"  actual:   {outcome.classification} / {outcome.method} / {outcome.status}")
    return failures


def check_readme_parse(readme: Path) -> list[str]:
    """Offline check that the three entries and their line numbers are parsed."""
    try:
        category, entries = parse_readme(readme.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        return [f"README parse failed: {error}"]

    failures = []
    if category != CATEGORY:
        failures.append(f"category: expected {CATEGORY!r}, got {category!r}")
    lines = readme.read_text(encoding="utf-8").splitlines()
    for name in SELECTED_NAMES:
        entry = entries.get(name)
        if entry is None:
            failures.append(f"missing entry: {name}")
        elif entry.line < 1 or entry.line > len(lines) or name not in lines[entry.line - 1]:
            failures.append(f"line number for {name} does not point at its README row: {entry.line}")
    print("README parse: category and three selected entries found")
    for name in SELECTED_NAMES:
        entry = entries.get(name)
        if entry:
            print(f"  {name}: {readme.name}:{entry.line}")
    return failures


def run_self_test(readme: Path, fixtures: Path) -> int:
    print("R02-T037 offline self-test")
    print(f"Fixtures: {fixtures}")
    print()

    failures: list[str] = []
    fixture_paths = sorted(fixtures.glob("*.json"))
    if not fixture_paths:
        failures.append(f"no JSON fixtures found in {fixtures}")

    for path in fixture_paths:
        try:
            fixture_failures = check_fixture(path)
        except (OSError, KeyError, ValueError, TypeError, AssertionError) as error:
            fixture_failures = [f"fixture error: {type(error).__name__}: {error}"]
        if fixture_failures:
            failures.extend(f"{path.name}: {message}" for message in fixture_failures)
            print("  FAIL")
        else:
            print("  PASS")
        print()

    print("README parser check")
    parser_failures = check_readme_parse(readme)
    if parser_failures:
        failures.extend(parser_failures)
        print("  FAIL")
    else:
        print("  PASS")
    print()

    if failures:
        print(f"SELF-TEST FAILED: {len(failures)} assertion(s)")
        for failure in failures:
            print(f"  - {failure}")
        return 1

    print(f"SELF-TEST PASSED: {len(fixture_paths)} fixtures, README parser check")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="R02-T037 availability checker and offline self-test")
    parser.add_argument("--readme", type=Path, default=REPO_ROOT / "README.md", help="README.md to parse")
    parser.add_argument("--timeout", type=float, default=10.0, help="per-request timeout in seconds (default: 10)")
    parser.add_argument("--self-test", action="store_true", help="run offline fixtures without network access")
    parser.add_argument(
        "--fixtures",
        type=Path,
        default=REPO_ROOT / "work" / "R02-T037" / "fixtures",
        help="fixture directory used by --self-test",
    )
    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error("--timeout must be greater than zero")
    if args.self_test:
        return run_self_test(args.readme, args.fixtures)
    return run_checks(args.readme, args.timeout)


if __name__ == "__main__":
    sys.exit(main())
