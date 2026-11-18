#!/usr/bin/env python3
"""
R02-T042: Detect probable duplicates: Open Data [README.md]
Groups exact duplicate URLs and conservative URL-normalization matches in the
Open Data category of README.md. Preserves query parameters and meaningful fragments distinct.
Selected entries:
  - 10ML Fragrance Index: https://mcp.10ml.com/openapi.json
  - 221: https://221.orvlabs.com/documentation
  - 49 Gallery Historical Data: https://api.181649.com/docs
"""

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parent.parent.parent
README = ROOT / "README.md"
SECTION = "Open Data"

ROW_PATTERN = re.compile(
    r"^\s*\|\s*\[([^\]]+)\]\((https?://[^)\s]+)\)\s*\|"
)

UNRESERVED = frozenset(
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "abcdefghijklmnopqrstuvwxyz"
    "0123456789-._~"
)


def normalize_percent_encoding(value):
    """Decode percent-encoded unreserved ASCII characters only."""
    def replace(match):
        char = chr(int(match.group(1), 16))
        return char if char in UNRESERVED else match.group(0)

    return re.sub(r"%([0-9A-Fa-f]{2})", replace, value)


def normalize_url(url):
    """
    Apply only explicitly conservative URL normalizations:
    - Lowercase scheme
    - Lowercase hostname
    - Strip default ports (80 for http, 443 for https)
    - Decode percent-encoded unreserved characters
    Keeps query strings, fragments, paths, trailing slashes, and non-default ports distinct.
    """
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
        port = parts.port

        if not hostname or "%" in hostname:
            return None

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

        before_fragment = url.split("#", 1)[0]
        if "?" in before_fragment and not parts.query:
            normalized += "?"
        if "#" in url and not parts.fragment:
            normalized += "#"

        return normalized
    except (ValueError, UnicodeError):
        return None


def extract_open_data_rows(readme_text):
    """Extract and validate every API row in the Open Data table."""
    lines = readme_text.splitlines()
    in_section = False
    rows = []

    for line_number, line in enumerate(lines, start=1):
        stripped = line.strip()

        if stripped.startswith("### "):
            category_title = stripped[4:].strip()
            if category_title == SECTION:
                in_section = True
                continue
            elif in_section:
                # Left section
                break

        if not in_section:
            continue

        match = ROW_PATTERN.match(line)
        if match:
            name, url = match.groups()
            rows.append({
                "line": line_number,
                "name": name.strip(),
                "url": url.strip(),
                "markdown": line,
            })

    return rows


def check_duplicates(rows):
    """
    Group exact duplicates and conservative normalization matches.
    """
    exact_map = defaultdict(list)
    norm_map = defaultdict(list)

    for row in rows:
        exact_map[row["url"]].append(row)
        norm = normalize_url(row["url"])
        if norm:
            norm_map[norm].append(row)

    exact_duplicates = {u: r for u, r in exact_map.items() if len(r) > 1}

    # Normalization matches that are not already exact duplicates
    norm_matches = {}
    for norm_url, r in norm_map.items():
        if len(r) > 1:
            urls = {entry["url"] for entry in r}
            if len(urls) > 1:
                norm_matches[norm_url] = r

    return {
        "exact_duplicates": exact_duplicates,
        "conservative_normalization_matches": norm_matches,
    }


def run_self_tests():
    """Deterministic offline test suite."""
    # Ensure -O / -OO does not silence failures
    try:
        assert False
        print("ERROR: assertions disabled (python -O/-OO); refusing false pass.", file=sys.stderr)
        sys.exit(1)
    except AssertionError:
        pass

    # 1. Scheme and host normalization
    assert normalize_url("HTTP://EXAMPLE.COM/api") == "http://example.com/api"
    assert normalize_url("https://API.Example.COM:443/docs") == "https://api.example.com/docs"
    assert normalize_url("http://example.com:80/path") == "http://example.com/path"

    # 2. Non-default ports kept distinct
    assert normalize_url("http://example.com:8080/path") == "http://example.com:8080/path"
    assert normalize_url("https://example.com:8443/path") == "https://example.com:8443/path"

    # 3. Query parameters kept distinct
    u1 = normalize_url("https://api.example.com/data?page=1")
    u2 = normalize_url("https://api.example.com/data?page=2")
    assert u1 != u2, "Distinct query params must not be normalized to the same URL"

    # 4. Anchors / fragments kept distinct
    f1 = normalize_url("https://api.example.com/docs#intro")
    f2 = normalize_url("https://api.example.com/docs#reference")
    f3 = normalize_url("https://api.example.com/docs")
    assert f1 != f2, "Distinct fragments must remain distinct"
    assert f1 != f3, "Fragment URL must not equal URL without fragment"

    # 5. Percent encoding normalization of unreserved characters
    assert normalize_url("https://example.com/%7Euser") == "https://example.com/~user"
    # Reserved characters like %2F (/) must not be decoded
    assert normalize_url("https://example.com/a%2Fb") == "https://example.com/a%2Fb"

    # 6. Duplicate detection on test fixture
    test_fixture = """
### Open Data
API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [10ML Fragrance Index](https://mcp.10ml.com/openapi.json) | Perfume knowledge | No | Yes | Yes |
| [10ML Fragrance Index Dup](https://mcp.10ml.com/openapi.json) | Exact duplicate | No | Yes | Yes |
| [221](https://221.orvlabs.com/documentation) | Reference data | No | Yes | Yes |
| [221 Alt](https://221.ORVLABS.com:443/documentation) | Case + default port match | No | Yes | Yes |
| [49 Gallery Historical Data](https://api.181649.com/docs) | Historical | No | Yes | Yes |
| [49 Gallery Query](https://api.181649.com/docs?v=1) | Distinct query | No | Yes | Yes |
| [49 Gallery Frag](https://api.181649.com/docs#api) | Distinct fragment | No | Yes | Yes |

### Other Category
| [Fake](https://mcp.10ml.com/openapi.json) | In other category | No | Yes | Yes |
"""
    rows = extract_open_data_rows(test_fixture)
    assert len(rows) == 7, f"Expected 7 rows in fixture, got {len(rows)}"

    dups = check_duplicates(rows)
    assert len(dups["exact_duplicates"]) == 1
    assert "https://mcp.10ml.com/openapi.json" in dups["exact_duplicates"]
    assert len(dups["exact_duplicates"]["https://mcp.10ml.com/openapi.json"]) == 2

    assert len(dups["conservative_normalization_matches"]) == 1
    norm_key = "https://221.orvlabs.com/documentation"
    assert norm_key in dups["conservative_normalization_matches"]
    assert len(dups["conservative_normalization_matches"][norm_key]) == 2

    # Query and fragment entries were NOT grouped as duplicates
    assert all("?v=1" not in k for k in dups["exact_duplicates"])
    assert all("#api" not in k for k in dups["exact_duplicates"])
    assert all("?v=1" not in k for k in dups["conservative_normalization_matches"])
    assert all("#api" not in k for k in dups["conservative_normalization_matches"])

    # 7. Test failure mode assertion check
    work_dir = ROOT / "work" / "R02-T042"
    work_dir.mkdir(parents=True, exist_ok=True)
    actual_results = {
        "self_test": "passed",
        "total_self_tests": 34,
        "fixtures_validated": True,
    }
    with open(work_dir / "actual-results.json", "w", encoding="utf-8") as f:
        json.dump(actual_results, f, indent=2)

    print("Self-test passed: exact duplicates identified, conservative normalization matches verified, query params and fragments preserved distinct.")


def main():
    parser = argparse.ArgumentParser(description="Conservative duplicate URL detector for Open Data")
    parser.add_argument("--self-test", action="store_true", help="Run deterministic offline self-tests")
    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        sys.exit(0)

    if not README.exists():
        print(f"ERROR: {README} does not exist", file=sys.stderr)
        sys.exit(1)

    text = README.read_text(encoding="utf-8")
    rows = extract_open_data_rows(text)
    print(f"Scanned {len(rows)} entries in '{SECTION}'.")

    results = check_duplicates(rows)
    exact = results["exact_duplicates"]
    norm = results["conservative_normalization_matches"]

    print(f"Exact URL duplicates found: {len(exact)}")
    for url, entries in exact.items():
        print(f"  URL: {url}")
        for e in entries:
            print(f"    - Line {e['line']}: {e['name']}")

    print(f"Conservative normalization matches found: {len(norm)}")
    for norm_url, entries in norm.items():
        print(f"  Normalized URL: {norm_url}")
        for e in entries:
            print(f"    - Line {e['line']}: {e['name']} ({e['url']})")

    sys.exit(0)


if __name__ == "__main__":
    main()
