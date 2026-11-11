#!/usr/bin/env python3
"""Bounded redirect verification for the assigned Data Validation APIs."""

import argparse
import json
import re
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURE = ROOT / "tools/course_checks/fixtures/r02-t022/redirect_cases.json"

SELECTED = {"VATlayer", "Attestwire", "invowerk"}
MAX_REDIRECTS = 5
TIMEOUT_SECONDS = 8


class RedirectLoopError(Exception):
    pass


class RedirectLimitError(Exception):
    pass


class TrackingRedirectHandler(urllib.request.HTTPRedirectHandler):
    def __init__(self):
        super().__init__()
        self.visited = set()
        self.chain = []

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not self.visited:
            self.visited.add(req.full_url)

        if newurl in self.visited:
            raise RedirectLoopError(f"Redirect loop detected at {newurl}")

        if len(self.chain) >= MAX_REDIRECTS:
            raise RedirectLimitError("Redirect limit exceeded")

        self.chain.append(code)
        self.visited.add(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def looks_like_login_wall(status, final_url, body):
    """Detect common login walls using status, URL and HTML indicators."""
    if status in (401, 403):
        return True

    url_path = (final_url or "").lower().split("?")[0].rstrip("/")
    if re.search(r"/(login|signin|sign-in|auth)(/|$)", url_path):
        return True

    content = (body or "").lower()
    indicators = (
        'type="password"',
        "name=\"password\"",
        "sign in to continue",
        "log in to continue",
        "please sign in",
        "login to your account",
        "log in to your account",
    )
    return any(marker in content for marker in indicators)


def classify(status, redirect_chain, error=None, final_url=None, body=""):
    """Classify a completed request or a known failure."""
    if error == "timeout":
        return "timeout"
    if error == "redirect_loop":
        return "redirect_loop"
    if error == "redirect_limit":
        return "redirect_limit"
    if error:
        return "request_error"

    if looks_like_login_wall(status, final_url, body):
        return "login_wall"

    if status is None:
        return "request_error"
    if status == 200:
        return "redirected" if redirect_chain else "ok"
    return "http_error"


def parse_selected_entries(readme_text):
    """Extract assigned entries only from the Data Validation section."""
    entries = []
    in_section = False

    for line_number, line in enumerate(readme_text.splitlines(), start=1):
        heading = re.match(r"^###\s+(.+?)\s*$", line)

        if heading:
            if in_section:
                break
            in_section = heading.group(1).strip() == "Data Validation"
            continue

        if not in_section:
            continue

        match = re.match(
            r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|"
            r"\s*(.*?)\s*\|\s*`([^`]*)`\s*\|"
            r"\s*(Yes|No)\s*\|\s*(Yes|No|Unknown)\s*\|",
            line,
        )
        if not match:
            continue

        name, url, description, auth, https, cors = match.groups()
        if name in SELECTED:
            entries.append({
                "name": name,
                "url": url,
                "description": description,
                "auth": auth,
                "https": https,
                "cors": cors,
                "category": "Data Validation",
                "line": line_number,
            })

    found = {entry["name"] for entry in entries}
    missing = SELECTED - found
    if missing:
        raise ValueError(
            "Missing assigned entries in Data Validation: "
            + ", ".join(sorted(missing))
        )

    return entries


def check_url(url):
    """Make one sequential GET request with a bounded redirect budget."""
    handler = TrackingRedirectHandler()
    opener = urllib.request.build_opener(handler)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "R02-T022-Redirect-Checker/1.0"},
    )

    status = None
    final_url = None
    body = ""

    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            final_url = response.geturl()
            body = response.read(65536).decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        status = exc.code
        final_url = exc.geturl()
        body = exc.read(65536).decode("utf-8", errors="replace")
        exc.close()
    except (TimeoutError, urllib.error.URLError) as exc:
        reason = getattr(exc, "reason", None)
        is_timeout = isinstance(exc, TimeoutError) or isinstance(reason, TimeoutError)
        error = "timeout" if is_timeout else "request_error"
        return {
            "status": None,
            "final_url": None,
            "redirect_chain": handler.chain,
            "result": error,
            "error": str(exc),
        }
    except RedirectLoopError as exc:
        return {
            "status": None,
            "final_url": None,
            "redirect_chain": handler.chain,
            "result": "redirect_loop",
            "error": str(exc),
        }
    except RedirectLimitError as exc:
        return {
            "status": None,
            "final_url": None,
            "redirect_chain": handler.chain,
            "result": "redirect_limit",
            "error": str(exc),
        }
    except Exception as exc:
        return {
            "status": None,
            "final_url": None,
            "redirect_chain": handler.chain,
            "result": "request_error",
            "error": str(exc),
        }

    result = classify(
        status, handler.chain, final_url=final_url, body=body
    )
    return {
        "status": status,
        "final_url": final_url,
        "redirect_chain": handler.chain,
        "result": result,
        "error": None,
    }


def run_self_tests():
    cases = json.loads(FIXTURE.read_text(encoding="utf-8"))

    for case in cases:
        actual = classify(
            case["status"],
            case["redirect_chain"],
            error=case.get("error"),
            final_url=case.get("final_url"),
            body=case.get("body", ""),
        )
        assert actual == case["expected"], (
            f'{case["name"]}: expected {case["expected"]}, got {actual}'
        )

    sample = """\
### Other
| [VATlayer](https://wrong.example) | Ignore | `No` | Yes | Yes |
### Data Validation
| [VATlayer](https://vatlayer.com/?x=1#docs) | VAT validation | `apiKey` | Yes | Unknown |
| [Attestwire](https://api.attestwire.com/docs) | Invoice validation | `apiKey` | Yes | Yes |
| [invowerk](https://invowerk.dev/docs) | E-invoice validation | `apiKey` | Yes | Unknown |
### Other Section
| [VATlayer](https://wrong-again.example) | Ignore | `No` | Yes | Yes |
"""
    entries = parse_selected_entries(sample)
    assert [entry["name"] for entry in entries] == [
        "VATlayer", "Attestwire", "invowerk"
    ]
    assert entries[0]["url"] == "https://vatlayer.com/?x=1#docs"
    assert [entry["line"] for entry in entries] == [4, 5, 6]

    print("All offline tests passed!")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline tests without making network requests",
    )
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    entries = parse_selected_entries(README.read_text(encoding="utf-8"))
    report = []

    for entry in entries:
        result = check_url(entry["url"])
        report.append({
            **entry,
            **result,
            "observed_at": date.today().isoformat(),
        })
        print(json.dumps(report[-1], indent=2))

    output = ROOT / "work/R02-T022/actual.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"\nLive report saved to {output.relative_to(ROOT)}")


if __name__ == "__main__":
    try:
        main()
    except (AssertionError, ValueError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
