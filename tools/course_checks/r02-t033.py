#!/usr/bin/env python3
"""Conservative, read-only duplicate URL checker for R02-T033."""

import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit


ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
SECTION = "Environment"

ROW_PATTERN = re.compile(
    r"^\s*\|\s*\[([^\]]+)\]\((https?://[^)\s]+)\)\s*\|"
)
UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-._~"
)


def markdown_unescape(value):
    """Undo Markdown backslash escapes in a link destination."""
    return re.sub(
        r"\\([!#$%&'()*+,\-./:;<=>?@\[\\\]^_`{|}~])",
        r"\1",
        value,
    )


def normalize_percent_encoding(value):
    """Decode percent-encoded unreserved ASCII characters only."""
    def replace(match):
        char = chr(int(match.group(1), 16))
        return char if char in UNRESERVED else match.group(0)

    return re.sub(r"%([0-9A-Fa-f]{2})", replace, value)


def normalize_url(url):
    """Apply only explicitly safe URL normalizations."""
    if not isinstance(url, str) or not url or any(c.isspace() for c in url):
        return None

    try:
        parts = urlsplit(url)
        scheme = parts.scheme.lower()

        if scheme not in ("http", "https") or not parts.netloc:
            return None
        if parts.username is not None or parts.password is not None:
            return None
        if parts.hostname is None:
            return None

        hostname = parts.hostname.lower()
        port = parts.port  # Raises ValueError for malformed ports.

        if not hostname or "%" in hostname:
            return None

        # Reject malformed bracket usage and empty explicit ports.
        if parts.netloc.count("[") != parts.netloc.count("]"):
            return None
        if parts.netloc.endswith(":"):
            return None

        if ":" in hostname and not hostname.startswith("["):
            hostname = "[" + hostname + "]"

        netloc = hostname
        if port is not None and not (
            (scheme == "http" and port == 80)
            or (scheme == "https" and port == 443)
        ):
            netloc += ":" + str(port)

        normalized = urlunsplit((
            scheme,
            netloc,
            normalize_percent_encoding(parts.path),
            parts.query,
            parts.fragment,
        ))

        # urlunsplit() drops explicitly empty query/fragment delimiters.
        before_fragment = url.split("#", 1)[0]
        if "?" in before_fragment and not parts.query:
            normalized += "?"
        if "#" in url and not parts.fragment:
            normalized += "#"

        return normalized
    except (ValueError, UnicodeError):
        return None


def extract_environment_rows(readme_text):
    """Extract and validate every API row in the Environment table."""
    lines = readme_text.splitlines()
    in_section = False
    found_section = False
    table_started = False
    rows = []

    for line_number, line in enumerate(lines, start=1):
        heading = re.match(r"^###\s+(.+?)\s*$", line)

        if heading:
            if in_section:
                break
            if heading.group(1) == SECTION:
                in_section = True
                found_section = True
            continue

        if not in_section:
            continue

        stripped = line.strip()

        if not stripped or stripped.startswith("**") or stripped.startswith("<"):
            if table_started and rows:
                break
            continue

        if stripped.startswith("|") and "API" in stripped and "Description" in stripped:
            table_started = True
            continue

        if stripped.startswith("|") and re.match(r"^\|[\s:| -]+\|?$", stripped):
            table_started = True
            continue

        if stripped.startswith("|"):
            table_started = True
            match = ROW_PATTERN.match(line)
            if not match:
                raise ValueError(
                    "Malformed Environment API row at line {}".format(line_number)
                )

            name = match.group(1)
            raw_url = match.group(2)
            url = markdown_unescape(raw_url)

            if normalize_url(url) is None:
                raise ValueError(
                    "Invalid HTTP(S) URL at Environment line {}".format(line_number)
                )

            rows.append({
                "name": name,
                "raw_url": raw_url,
                "url": url,
                "line": line_number,
                "markdown": line,
            })

    if not found_section:
        raise ValueError("Environment section was not found")
    if not rows:
        raise ValueError("Environment section contains no API rows")

    return rows


def group_duplicates(rows, key_function, url_field="url"):
    """Group rows by URL key, retaining only groups with 2+ entries."""
    groups = defaultdict(list)

    for row in rows:
        key = key_function(row[url_field])
        if key is not None:
            groups[key].append(row)

    return {
        key: members
        for key, members in groups.items()
        if len(members) > 1
    }


def build_report(rows):
    """Build a report string; never writes to the repository."""
    exact = group_duplicates(rows, lambda url: url, "raw_url")
    normalized = group_duplicates(rows, normalize_url)

    output = [
        "R02-T033 — Environment URL duplicate report",
        "Entries scanned: {}".format(len(rows)),
        "",
        "Exact URL duplicates:",
    ]

    if not exact:
        output.append("  None found.")
    else:
        for url, members in exact.items():
            output.extend(["", "  URL: " + url])
            for row in members:
                output.append("  - {} (line {})".format(row["name"], row["line"]))
                output.append("    " + row["markdown"])

    output.extend(["", "Conservative normalization matches:"])
    additional = []

    for key, members in normalized.items():
        if len({row["url"] for row in members}) > 1:
            additional.append((key, members))

    if not additional:
        output.append("  None found.")
    else:
        for key, members in additional:
            output.extend(["", "  Normalized URL: " + key])
            for row in members:
                output.append("  - {} (line {})".format(row["name"], row["line"]))
                output.append("    Original URL: " + row["url"])
                output.append("    " + row["markdown"])

    output.extend([
        "",
        "Manual review is required for every reported match.",
        "No catalogue entries were changed or marked for automatic deletion.",
    ])
    return "\n".join(output)


def run_self_tests():
    checks = []

    def check(name, condition):
        checks.append((name, bool(condition)))

    check("scheme and hostname case",
          normalize_url("HTTPS://EXAMPLE.COM/a") == "https://example.com/a")
    check("default HTTPS port",
          normalize_url("https://example.com:443/a") == "https://example.com/a")
    check("default HTTP port",
          normalize_url("http://example.com:80/a") == "http://example.com/a")
    check("non-default ports remain distinct",
          normalize_url("https://example.com:8443/a") != normalize_url("https://example.com/a"))
    check("query values remain distinct",
          normalize_url("https://example.com/a?x=1") != normalize_url("https://example.com/a?x=2"))
    check("query names remain distinct",
          normalize_url("https://example.com/a?x=1") != normalize_url("https://example.com/a?y=1"))
    check("query order remains distinct",
          normalize_url("https://example.com/a?x=1&y=2") != normalize_url("https://example.com/a?y=2&x=1"))
    check("duplicate query parameters remain distinct",
          normalize_url("https://example.com/a?x=1&x=2") != normalize_url("https://example.com/a?x=1"))
    check("fragments remain distinct",
          normalize_url("https://example.com/a#one") != normalize_url("https://example.com/a#two"))
    check("fragment and no fragment remain distinct",
          normalize_url("https://example.com/a#one") != normalize_url("https://example.com/a"))
    check("different paths remain distinct",
          normalize_url("https://example.com/a") != normalize_url("https://example.com/b"))
    check("trailing slash remains distinct",
          normalize_url("https://example.com/a") != normalize_url("https://example.com/a/"))
    check("unreserved percent encoding is normalized",
          normalize_url("https://example.com/%7Euser") == normalize_url("https://example.com/~user"))
    check("reserved percent encoding is not decoded",
          normalize_url("https://example.com/%2F") != normalize_url("https://example.com//"))
    check("empty query delimiter remains distinct",
          normalize_url("https://example.com/a?") != normalize_url("https://example.com/a"))
    check("empty fragment delimiter remains distinct",
          normalize_url("https://example.com/a#") != normalize_url("https://example.com/a"))
    check("empty query and fragment delimiters remain distinct",
          normalize_url("https://example.com/a?#") != normalize_url("https://example.com/a"))

    for invalid in (
        "not a URL",
        "https:///missing-host",
        "https://example.com:bad/path",
        "https://user:pass@example.com/",
        "https://example.com:/",
        "https://example.com/a b",
    ):
        check("invalid URL rejected: " + invalid, normalize_url(invalid) is None)

    exact_rows = [
        {
            "name": "Example A",
            "raw_url": "https://example.com/a",
            "url": "https://example.com/a",
            "line": 10,
            "markdown": "| [Example A](https://example.com/a) | description |",
        },
        {
            "name": "Example B",
            "raw_url": "https://example.com/a",
            "url": "https://example.com/a",
            "line": 11,
            "markdown": "| [Example B](https://example.com/a) | description |",
        },
        {
            "name": "Example C",
            "raw_url": "https://example.com/b",
            "url": "https://example.com/b",
            "line": 12,
            "markdown": "| [Example C](https://example.com/b) | description |",
        },
    ]
    check("exact duplicate grouping",
          len(group_duplicates(exact_rows, lambda url: url)) == 1)

    normalized_rows = [
        {"url": "HTTPS://EXAMPLE.COM:443/a"},
        {"url": "https://example.com/a"},
    ]
    check("normalized duplicate grouping",
          len(group_duplicates(normalized_rows, normalize_url)) == 1)

    sample = "\n".join([
        "### Other",
        r"| [Outside](https://example.com/outside) | description |",
        "### Environment",
        "API | Description | Auth | HTTPS | CORS |",
        "|:---|:---|:---|:---|:---|",
        r"| [AirNow](https://docs.airnowapi.org/) | description |",
        r"| [Tempo](https://www.calendrier-tempo.fr/api-tempo) | description |",
        "### Events",
        r"| [Event](https://example.com/event) | description |",
    ])
    extracted = extract_environment_rows(sample)

    check("section scope is limited",
          [row["name"] for row in extracted] == ["AirNow", "Tempo"])
    check("source line numbers are preserved",
          [row["line"] for row in extracted] == [6, 7])
    check("original Markdown row is preserved",
          extracted[1]["markdown"] == r"| [Tempo](https://www.calendrier-tempo.fr/api-tempo) | description |")
    check("missing section fails",
          _raises_value_error(lambda: extract_environment_rows("### Events\n| [X](https://x.test) |")))
    check("empty section fails",
          _raises_value_error(lambda: extract_environment_rows("### Environment\nAPI | Description\n### Events")))
    check("malformed API row fails",
          _raises_value_error(lambda: extract_environment_rows("### Environment\nAPI | Description\n| broken row\n### Events")))

    report = build_report(exact_rows)
    check("report requires manual review",
          "Manual review is required" in report)
    check("report explicitly forbids automatic deletion",
          "No catalogue entries were changed" in report)
    check("report retains source row and line",
          "line" in report and "https://example.com/a" in report)

    failed = [name for name, passed in checks if not passed]
    for name, passed in checks:
        print(("PASS" if passed else "FAIL") + ": " + name)

    print("\nSelf-test: {}/{} passed".format(len(checks) - len(failed), len(checks)))
    return 1 if failed else 0


def _raises_value_error(function):
    try:
        function()
    except ValueError:
        return True
    return False


def main():
    if sys.argv[1:] == ["--self-test"]:
        return run_self_tests()

    if sys.argv[1:]:
        print("Usage: python3 tools/course_checks/r02-t033.py [--self-test]")
        return 2

    try:
        rows = extract_environment_rows(README.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as error:
        print("ERROR: " + str(error))
        return 1

    print(build_report(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
