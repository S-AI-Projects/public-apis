import argparse
import json
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

FIXTURE_DIR = ROOT / "work" / "R02-T031" / "fixtures"

TARGET_NAMES = {
    "4chan",
    "API Direct",
    "Ayrshare",
}

LINK_PATTERN = re.compile(
    r"\[([^\]]+)\]\((https?://[^)\s]+)\)"
)

HEADING_PATTERN = re.compile(
    r"^\s{0,3}(#{1,6})[ \t]+(.+?)[ \t]*#*[ \t]*$"
)

# Opening fence: up to three spaces, then at least three
# backticks or tildes, followed by an optional info string.
OPEN_FENCE_PATTERN = re.compile(
    r"^ {0,3}(`{3,}|~{3,})(.*)$"
)

# Closing fence: matching marker followed ONLY by spaces/tabs.
# A line such as ```python therefore cannot close a fence.
CLOSE_FENCE_PATTERN = re.compile(
    r"^ {0,3}(`{3,}|~{3,})[ \t]*$"
)


def split_table_row(line):
    """Split a Markdown table row while respecting escaped pipes."""

    line = line.strip()

    if line.startswith("|"):
        line = line[1:]

    if line.endswith("|") and not line.endswith(r"\|"):
        line = line[:-1]

    cells = []
    current = []
    escaped = False

    for char in line:
        if char == "|" and not escaped:
            cells.append("".join(current).strip())
            current = []
        else:
            current.append(char)

        if char == "\\" and not escaped:
            escaped = True
        else:
            escaped = False

    cells.append("".join(current).strip())

    return cells


def clean_cell(value):
    """Remove whitespace and inline-code delimiters."""

    return value.strip().strip("`").strip()


def match_opening_fence(line):
    """Return (marker character, marker length) for an opening fence."""

    match = OPEN_FENCE_PATTERN.match(line)

    if not match:
        return None

    marker, info_string = match.groups()

    # CommonMark does not allow backticks in the info string
    # of a backtick fence. Such a line is not a fence opener.
    if marker[0] == "`" and "`" in info_string:
        return None

    return marker[0], len(marker)


def is_closing_fence(line, fence_char, fence_length):
    """Whether line validly closes the currently open fence."""

    match = CLOSE_FENCE_PATTERN.match(line)

    if not match:
        return False

    marker = match.group(1)

    return (
        marker[0] == fence_char
        and len(marker) >= fence_length
    )


def extract_entries(markdown):
    """Extract selected API entries from Markdown."""

    entries = []

    category = None
    headers = None

    fence_char = None
    fence_length = 0

    for line_number, line in enumerate(
        markdown.splitlines(),
        start=1,
    ):

        # -------------------------------------------------
        # Ignore content inside fenced code blocks.
        #
        # A closing fence must use the same marker character
        # and be at least as long as the opening fence. It may
        # only be followed by spaces/tabs; trailing info text is
        # code content, not a closing fence.
        # -------------------------------------------------

        if fence_char:

            if is_closing_fence(
                line,
                fence_char,
                fence_length,
            ):
                fence_char = None
                fence_length = 0

                # Do not let a table header inside the code block
                # attach itself to rows after the fence closes.
                headers = None

            # Never parse content inside an open fence.
            continue

        # -------------------------------------------------
        # Detect opening fenced code blocks.
        # -------------------------------------------------

        opening_fence = match_opening_fence(line)

        if opening_fence:
            fence_char, fence_length = opening_fence

            headers = None
            continue

        # -------------------------------------------------
        # Detect Markdown headings.
        # -------------------------------------------------

        heading_match = HEADING_PATTERN.match(line)

        if heading_match:

            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()

            if level == 3:
                category = heading_text
            else:
                category = None

            headers = None
            continue

        # -------------------------------------------------
        # Ignore empty lines and non-table lines.
        # -------------------------------------------------

        if not line.strip() or "|" not in line:
            headers = None
            continue

        cells = split_table_row(line)

        if not cells:
            continue

        normalized_headers = [
            clean_cell(cell).lower()
            for cell in cells
        ]

        # -------------------------------------------------
        # Detect table header.
        # -------------------------------------------------

        if (
            normalized_headers[0] in {"api", "name"}
            and any(
                "description" in cell
                for cell in normalized_headers
            )
        ):
            headers = normalized_headers
            continue

        # -------------------------------------------------
        # Ignore Markdown table separators.
        # -------------------------------------------------

        if all(
            re.fullmatch(
                r":?-{3,}:?",
                cell.replace(" ", ""),
            )
            for cell in cells
        ):
            continue

        if headers is None:
            continue

        if len(cells) != len(headers):
            continue

        # -------------------------------------------------
        # Extract API name and URL.
        # -------------------------------------------------

        link_match = LINK_PATTERN.search(cells[0])

        if not link_match:
            continue

        display_name, url = link_match.groups()

        # Only extract assigned entries from Social.
        if (
            display_name not in TARGET_NAMES
            or category != "Social"
        ):
            continue

        # -------------------------------------------------
        # Extract available metadata dynamically.
        # -------------------------------------------------

        metadata = {}

        for header, value in zip(
            headers[1:],
            cells[1:],
        ):

            key = re.sub(
                r"[^a-z0-9]+",
                "_",
                header,
            ).strip("_")

            if key:
                metadata[key] = clean_cell(value)

        entries.append(
            {
                "display_name": display_name,
                "url": url,
                "category": category,
                "source_line": line_number,
                "metadata": metadata,
            }
        )

    return entries


def require(condition, message):
    """Raise an assertion error when a test condition fails."""

    if not condition:
        raise AssertionError(message)


def table_lines(*rows, heading="### Social"):
    """Build a Markdown table as a list of lines."""

    return [
        heading,
        "",
        "API | Description | Auth | HTTPS | CORS |",
        "|---|---|---|---|---|",
        *rows,
        "",
    ]


def table_row(name, url, description="Test row"):
    """Build one Markdown table row."""

    return (
        f"| [{name}]({url}) | {description} "
        "| No | Yes | Yes |"
    )


def require_urls(markdown, expected_urls, case_name):
    """Extract entries and assert their URL list exactly."""

    entries = extract_entries(markdown)
    urls = [entry["url"] for entry in entries]

    require(
        urls == expected_urls,
        (
            f"{case_name}: expected URLs "
            f"{expected_urls}, got {urls}"
        ),
    )

    return entries


def run_fence_tests():
    """Exercise fence edge cases that are hard to see in input.md."""

    # -------------------------------------------------
    # Backtick fence: same marker closes; content before
    # and after the fence is still parsed.
    # -------------------------------------------------

    case = "\n".join(
        [
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/backtick-before",
                )
            ),
            "```markdown",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/backtick-inside",
                )
            ),
            "```",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/backtick-after",
                )
            ),
        ]
    )

    entries = require_urls(
        case,
        [
            "https://example.com/backtick-before",
            "https://example.com/backtick-after",
        ],
        "backtick fence",
    )

    require(
        all(
            entry["category"] == "Social"
            for entry in entries
        ),
        "backtick fence changed the active category",
    )

    # -------------------------------------------------
    # Tilde fence: same marker closes.
    # -------------------------------------------------

    case = "\n".join(
        [
            "~~~markdown",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/tilde-inside",
                )
            ),
            "~~~",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/tilde-after",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/tilde-after"],
        "tilde fence",
    )

    # -------------------------------------------------
    # A different marker character must not close a fence,
    # even when it is longer than the opening fence.
    # -------------------------------------------------

    case = "\n".join(
        [
            "```markdown",
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/wrong-marker-before",
                )
            ),
            "~~~~",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/wrong-marker-after",
                )
            ),
            "```",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/wrong-marker-outside",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/wrong-marker-outside"],
        "different closing marker",
    )

    # -------------------------------------------------
    # A closing fence shorter than the opening fence must
    # not close it. A full table after the short marker
    # makes a premature close visible.
    # -------------------------------------------------

    case = "\n".join(
        [
            "````markdown",
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/short-close-before",
                )
            ),
            "```",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/short-close-after",
                )
            ),
            "````",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/short-close-outside",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/short-close-outside"],
        "short closing fence",
    )

    # -------------------------------------------------
    # A closing fence with trailing language/info text is
    # not a closing fence. This is the nested-fence case.
    # -------------------------------------------------

    case = "\n".join(
        [
            "```markdown",
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/info-close-before",
                )
            ),
            "```python",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/info-close-after",
                )
            ),
            "```",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/info-close-outside",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/info-close-outside"],
        "closing fence with info text",
    )

    # -------------------------------------------------
    # A longer fence with the same marker is a valid close.
    # -------------------------------------------------

    case = "\n".join(
        [
            "```markdown",
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/long-close-inside",
                )
            ),
            "`````",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/long-close-outside",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/long-close-outside"],
        "longer closing fence",
    )

    # -------------------------------------------------
    # An unclosed fence runs to the end of the document.
    # -------------------------------------------------

    case = "\n".join(
        [
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/unclosed-before",
                )
            ),
            "```markdown",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/unclosed-inside",
                )
            ),
        ]
    )

    require_urls(
        case,
        ["https://example.com/unclosed-before"],
        "unclosed fence",
    )

    # -------------------------------------------------
    # Headings inside a fence must not change the category,
    # and headings after it closes must. Also proves that a
    # category change after the fence is still enforced.
    # -------------------------------------------------

    case = "\n".join(
        [
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/category-before",
                )
            ),
            "```markdown",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/category-inside",
                ),
                heading="### Development",
            ),
            "```",
            *table_lines(
                table_row(
                    "API Direct",
                    "https://example.com/category-after",
                )
            ),
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/category-development",
                ),
                heading="### Development",
            ),
        ]
    )

    entries = require_urls(
        case,
        [
            "https://example.com/category-before",
            "https://example.com/category-after",
        ],
        "category tracking around fence",
    )

    require(
        [
            entry["category"]
            for entry in entries
        ] == ["Social", "Social"],
        "category tracking around a fence is wrong",
    )

    # -------------------------------------------------
    # A malformed backtick opener (backticks in its info
    # string) must not start a fence.
    # -------------------------------------------------

    case = "\n".join(
        [
            *table_lines(
                table_row(
                    "4chan",
                    "https://example.com/malformed-before",
                )
            ),
            "```not`a`fence",
            *table_lines(
                table_row(
                    "Ayrshare",
                    "https://example.com/malformed-after",
                )
            ),
        ]
    )

    require_urls(
        case,
        [
            "https://example.com/malformed-before",
            "https://example.com/malformed-after",
        ],
        "malformed backtick opener",
    )


def run_self_test():
    """Run offline tests using the provided fixtures."""

    # Python -O and -OO disable assert statements.
    # Refuse to report a false pass in those modes.
    if not __debug__:
        print(
            "ERROR: assertions are disabled "
            "(python -O/-OO); refusing to report a "
            "false pass.",
            file=sys.stderr,
        )
        sys.exit(1)

    fixture_path = FIXTURE_DIR / "input.md"
    expected_path = FIXTURE_DIR / "expected.json"
    no_match_path = FIXTURE_DIR / "no-match.md"

    actual_path = (
        ROOT
        / "work"
        / "R02-T031"
        / "actual.json"
    )

    # -------------------------------------------------
    # Load fixtures.
    # -------------------------------------------------

    markdown = fixture_path.read_text(
        encoding="utf-8"
    )

    expected = json.loads(
        expected_path.read_text(
            encoding="utf-8"
        )
    )

    # Ensure the fixture genuinely contains all cases.
    required_fixture_tokens = [
        "https://example.com/blogger",
        "https://example.com/wrong-category",
        "https://example.com/backtick-fenced",
        "https://example.com/tilde-fenced",
        "https://example.com/tilde-fenced-2",
        "https://example.com/inside-nested-fence",
        "https://example.com/after-invalid-closing-fence",
        "https://example.com/inside-short-close-fence",
        "https://example.com/after-short-close-fence",
        "https://example.com/inside-info-close-fence",
        "https://example.com/after-info-close-fence",
        "https://example.com/inside-wrong-marker-fence",
        "https://example.com/after-wrong-marker-fence",
    ]

    for token in required_fixture_tokens:
        require(
            token in markdown,
            f"fixture is missing test case: {token}",
        )

    require(
        "```" in markdown,
        "fixture does not contain a backtick fence",
    )

    require(
        "~~~" in markdown,
        "fixture does not contain a tilde fence",
    )

    require(
        "````" in markdown,
        "fixture does not contain a longer opening fence",
    )

    require(
        "```python" in markdown,
        "fixture does not contain an invalid closing fence",
    )

    # -------------------------------------------------
    # Extract actual results.
    # -------------------------------------------------

    actual = extract_entries(markdown)

    actual_path.write_text(
        json.dumps(
            actual,
            indent=2,
            ensure_ascii=False,
        ) + "\n",
        encoding="utf-8",
    )

    # -------------------------------------------------
    # Success cases.
    # -------------------------------------------------

    require(
        actual == expected,
        (
            "Self-test failed.\n"
            f"Expected:\n{json.dumps(expected, indent=2)}\n"
            f"Actual:\n{json.dumps(actual, indent=2)}"
        ),
    )

    require(
        len(actual) == 3,
        f"expected 3 entries, got {len(actual)}",
    )

    require(
        [
            entry["display_name"] for entry in actual
        ] == ["4chan", "API Direct", "Ayrshare"],
        "unexpected display names or ordering",
    )

    require(
        [
            entry["source_line"] for entry in actual
        ] == [7, 8, 9],
        "source_line mapping is wrong",
    )

    require(
        all(
            entry["category"] == "Social"
            for entry in actual
        ),
        "an entry was not scoped to the Social section",
    )

    for entry in actual:

        require(
            bool(entry["metadata"]),
            f"missing metadata for {entry['display_name']}",
        )

        require(
            set(entry["metadata"]) == {
                "description",
                "auth",
                "https",
                "cors",
            },
            (
                f"unexpected metadata keys for "
                f"{entry['display_name']}: "
                f"{sorted(entry['metadata'])}"
            ),
        )

    # -------------------------------------------------
    # URL fragment preservation.
    # -------------------------------------------------

    api_direct = next(
        entry
        for entry in actual
        if entry["display_name"] == "API Direct"
    )

    require(
        api_direct["url"]
        == "https://apidirect.io/docs#overview",
        f"fragment lost: {api_direct['url']}",
    )

    # -------------------------------------------------
    # Failure cases: these must NOT be extracted.
    # -------------------------------------------------

    urls = {
        entry["url"]
        for entry in actual
    }

    forbidden = {
        "https://example.com/blogger":
            "non-assigned Social entry leaked",

        "https://example.com/wrong-category":
            "wrong-category entry leaked",

        "https://example.com/backtick-fenced":
            "backtick-fenced entry leaked",

        "https://example.com/tilde-fenced":
            "tilde-fenced entry leaked",

        "https://example.com/tilde-fenced-2":
            "tilde-fenced entry leaked",

        "https://example.com/fake":
            "fake link leaked",

        "https://example.com/inside-nested-fence":
            "entry before an invalid closing fence leaked",

        "https://example.com/after-invalid-closing-fence":
            "entry after an invalid closing fence leaked",

        "https://example.com/inside-short-close-fence":
            "entry before a short closing fence leaked",

        "https://example.com/after-short-close-fence":
            "entry after a short closing fence leaked",

        "https://example.com/inside-info-close-fence":
            "entry before an info-text closing fence leaked",

        "https://example.com/after-info-close-fence":
            "entry after an info-text closing fence leaked",

        "https://example.com/inside-wrong-marker-fence":
            "entry before a wrong-marker closing fence leaked",

        "https://example.com/after-wrong-marker-fence":
            "entry after a wrong-marker closing fence leaked",
    }

    for url, message in forbidden.items():
        require(url not in urls, message)

    require(
        all(
            entry["display_name"] != "Fake API"
            for entry in actual
        ),
        "fake link leaked",
    )

    # -------------------------------------------------
    # Fence edge cases.
    # -------------------------------------------------

    run_fence_tests()

    # -------------------------------------------------
    # Failure input: no assigned entries.
    # -------------------------------------------------

    no_match = extract_entries(
        no_match_path.read_text(encoding="utf-8")
    )

    require(
        no_match == [],
        f"no-match fixture yielded entries: {no_match}",
    )

    # A no-match input must make the CLI exit non-zero.
    result = subprocess.run(
        [
            sys.executable,
            str(Path(__file__).resolve()),
            "--input",
            str(no_match_path),
        ],
        capture_output=True,
        text=True,
    )

    require(
        result.returncode != 0,
        (
            "parser exited 0 for an input with no "
            "assigned entries"
        ),
    )

    # -------------------------------------------------
    # Report.
    # -------------------------------------------------

    print(
        "Self-test passed: 3 Social APIs extracted; "
        "wrong-category, non-assigned, fenced and fake "
        "links ignored; URL fragment preserved; "
        "source lines 7/8/9."
    )

    print(
        "Fence regression tests passed: backtick, tilde, "
        "wrong marker, short close, info-text close, "
        "longer close, unclosed fence, category tracking."
    )

    print(
        "Failure input rejected with a non-zero exit code."
    )

    print(
        f"Actual results written to: "
        f"{actual_path.relative_to(ROOT)}"
    )


def main():

    parser = argparse.ArgumentParser(
        description=__doc__
    )

    parser.add_argument(
        "--input",
        type=Path,
        default=ROOT / "README.md",
        help="Markdown file to parse.",
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline fixture tests.",
    )

    args = parser.parse_args()

    try:

        if args.self_test:
            run_self_test()
            return

        markdown = args.input.read_text(
            encoding="utf-8"
        )

        results = extract_entries(markdown)

        print(
            json.dumps(
                results,
                indent=2,
                ensure_ascii=False,
            )
        )

        if not results:
            print(
                "No assigned entries found.",
                file=sys.stderr,
            )
            sys.exit(1)

    except (
        OSError,
        json.JSONDecodeError,
        AssertionError,
    ) as error:

        print(
            f"ERROR: {error}",
            file=sys.stderr,
        )

        sys.exit(1)


if __name__ == "__main__":
    main()
