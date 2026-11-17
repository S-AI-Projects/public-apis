#!/usr/bin/env python3
"""Validate the three R02-T036 API entries in the README Vehicle table.

The checker is deliberately self-contained: it uses only the Python standard
library and reads README.md as plain UTF-8 text.  Run it with --self-test to
exercise the parser against the offline fixtures in work/R02-T036/fixtures/.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urlsplit

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_README = REPO_ROOT / "README.md"
FIXTURES_DIR = REPO_ROOT / "work" / "R02-T036" / "fixtures"

CATEGORY_HEADING = "### Vehicle"
EXPECTED_HEADERS = ("api", "description", "auth", "https", "cors")
VALID_AUTH = {"No", "apiKey", "OAuth", "X-Mashape-Key", "User-Agent"}
VALID_HTTPS = {"Yes", "No"}
VALID_CORS = {"Yes", "No", "Unknown"}
FIELD_LABELS = {"url": "URL", "auth": "Auth", "https": "HTTPS", "cors": "CORS"}


@dataclass(frozen=True)
class ExpectedEntry:
    name: str
    url: str
    auth: str
    https: str
    cors: str


SELECTED = (
    ExpectedEntry(
        "Auto Body Shop Directory",
        "https://autobodyshopnear.com/developers/body-shop-api",
        "No",
        "Yes",
        "No",
    ),
    ExpectedEntry(
        "Bike Reliability",
        "https://bikereliability.co.uk/developers",
        "No",
        "Yes",
        "Yes",
    ),
    ExpectedEntry(
        "BoltPatternHQ",
        "https://boltpatternhq.com/mcp/",
        "No",
        "Yes",
        "Yes",
    ),
)
SELECTED_BY_NAME = {entry.name: entry for entry in SELECTED}


@dataclass(frozen=True)
class Issue:
    line: Optional[int]
    message: str


@dataclass
class Row:
    line: int
    name: str
    url: str
    description: str
    auth: str
    https: str
    cors: str


@dataclass
class Report:
    heading_line: Optional[int] = None
    header_line: Optional[int] = None
    separator_line: Optional[int] = None
    table_end_line: Optional[int] = None
    rows: List[Row] = field(default_factory=list)
    selected: Dict[str, Row] = field(default_factory=dict)
    seen_selected: Set[str] = field(default_factory=set)
    issues: List[Issue] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.issues


def add_issue(report: Report, line: Optional[int], message: str) -> None:
    report.issues.append(Issue(line, message))


def split_table_row(line: str) -> List[str]:
    """Split a Markdown table row without breaking links or escaped pipes.

    Pipes inside link text, link destinations (including balanced parentheses),
    angle-bracket destinations, code spans, and backslash escapes are treated as
    literal text.  Leading/trailing table delimiters are removed.
    """
    text = line.strip()
    cells: List[str] = []
    current: List[str] = []
    escaped = False
    in_code = False
    bracket_depth = 0
    link_depth = 0
    in_angle = False
    index = 0

    while index < len(text):
        char = text[index]

        if escaped:
            current.append(char)
            escaped = False
            index += 1
            continue

        if char == "\\":
            current.append(char)
            escaped = True
            index += 1
            continue

        if in_code:
            current.append(char)
            if char == "`":
                in_code = False
            index += 1
            continue

        if link_depth:
            current.append(char)
            if in_angle:
                if char == ">":
                    in_angle = False
            elif char == "<":
                in_angle = True
            elif char == "(":
                link_depth += 1
            elif char == ")":
                link_depth -= 1
            index += 1
            continue

        if char == "`":
            in_code = True
            current.append(char)
            index += 1
            continue

        if char == "[":
            bracket_depth += 1
            current.append(char)
            index += 1
            continue

        if char == "]":
            if bracket_depth:
                bracket_depth -= 1
            current.append(char)
            if bracket_depth == 0 and index + 1 < len(text) and text[index + 1] == "(":
                current.append("(")
                index += 2
                link_depth = 1
                in_angle = False
                continue
            index += 1
            continue

        if char == "|" and bracket_depth == 0:
            cells.append("".join(current))
            current = []
            index += 1
            continue

        current.append(char)
        index += 1

    cells.append("".join(current))

    if text.startswith("|") and cells and not cells[0].strip():
        cells.pop(0)
    if text.endswith("|") and cells and not cells[-1].strip():
        cells.pop()
    return cells


def unescape_markdown_url(url: str) -> str:
    """Turn Markdown escapes for parentheses/backslashes into URL characters."""
    return re.sub(r"\\([\\()])", r"\1", url)


def parse_markdown_link(cell: str) -> Tuple[str, str]:
    """Return (link text, URL) for a single [text](url) Markdown link."""
    text = cell.strip()
    if not text:
        raise ValueError("is empty")
    if not text.startswith("["):
        raise ValueError("is not a Markdown link; expected [name](url)")

    index = 1
    depth = 0
    while index < len(text):
        char = text[index]
        if char == "\\":
            index += 2
            continue
        if char == "[":
            depth += 1
        elif char == "]":
            if depth == 0:
                break
            depth -= 1
        index += 1

    if index >= len(text):
        raise ValueError("has no closing ']'")

    name = text[1:index].strip()
    if not name:
        raise ValueError("has empty link text")

    index += 1
    if index >= len(text) or text[index] != "(":
        raise ValueError("has no '(url)' after link text")
    index += 1
    while index < len(text) and text[index].isspace():
        index += 1
    if index >= len(text):
        raise ValueError("has no URL")

    if text[index] == "<":
        end = text.find(">", index + 1)
        if end == -1:
            raise ValueError("has an unterminated angle-bracket URL")
        url = text[index + 1:end]
        index = end + 1
    else:
        start = index
        depth = 1
        end = None
        while index < len(text):
            char = text[index]
            if char == "\\":
                index += 2
                continue
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    end = index
                    break
            elif char.isspace():
                end = index
                break
            index += 1
        if end is None:
            raise ValueError("has an unterminated URL")
        url = text[start:end]
        index = end

    url = unescape_markdown_url(url)

    while index < len(text) and text[index].isspace():
        index += 1

    if index < len(text) and text[index] == ")":
        index += 1
    else:
        if index >= len(text):
            raise ValueError("has no closing ')'")
        if text[index] in "\"'":
            quote = text[index]
            index += 1
            while index < len(text) and text[index] != quote:
                if text[index] == "\\":
                    index += 2
                else:
                    index += 1
            if index >= len(text):
                raise ValueError("has an unterminated title")
            index += 1
        elif text[index] == "(":
            depth = 1
            index += 1
            while index < len(text) and depth:
                if text[index] == "(":
                    depth += 1
                elif text[index] == ")":
                    depth -= 1
                index += 1
            if depth:
                raise ValueError("has an unterminated title")
        else:
            raise ValueError("has unexpected text after the URL")

        while index < len(text) and text[index].isspace():
            index += 1
        if index >= len(text) or text[index] != ")":
            raise ValueError("has no closing ')'")
        index += 1

    if index != len(text):
        raise ValueError("has unexpected text after the closing ')'")
    if not url:
        raise ValueError("has an empty URL")
    return name, url


def extract_link_name(cell: str) -> Optional[str]:
    """Best-effort name extraction for malformed rows."""
    try:
        return parse_markdown_link(cell)[0]
    except ValueError:
        match = re.match(r"\[\s*([^\]]+?)\s*\]", cell.strip())
        return match.group(1) if match else None


def normalize_code(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value.startswith("`") and value.endswith("`"):
        value = value[1:-1].strip()
    return value


def url_problem(url: str) -> Optional[str]:
    if not url:
        return "URL is empty"
    if any(char.isspace() or ord(char) < 0x20 for char in url):
        return "URL contains whitespace or control characters"
    if re.search(r"%(?![0-9A-Fa-f]{2})", url):
        return "URL contains an invalid percent escape"
    try:
        parts = urlsplit(url)
    except ValueError as exc:
        return "URL is invalid: {}".format(exc)
    if parts.scheme.lower() not in ("http", "https"):
        return "URL scheme must be http or https"
    if not parts.netloc:
        return "URL must include a host"
    return None


def check_allowed(
    report: Report,
    line_number: int,
    name: str,
    field: str,
    value: str,
    allowed: Set[str],
    allowed_text: str,
) -> None:
    if not value:
        add_issue(report, line_number, "{}: {} is empty".format(name, field))
    elif value not in allowed:
        add_issue(
            report,
            line_number,
            "{}: {} must be {}; found {!r}".format(name, field, allowed_text, value),
        )


def validate_row(report: Report, line: str, line_number: int) -> None:
    cells = split_table_row(line)
    if len(cells) != 5:
        add_issue(report, line_number, "expected 5 cells, found {}".format(len(cells)))
        if cells:
            name = extract_link_name(cells[0])
            if name in SELECTED_BY_NAME:
                report.seen_selected.add(name)
        return

    try:
        name, url = parse_markdown_link(cells[0])
    except ValueError as exc:
        add_issue(report, line_number, "API cell {}".format(exc))
        name = extract_link_name(cells[0])
        if name in SELECTED_BY_NAME:
            report.seen_selected.add(name)
        return

    description = cells[1].strip()
    auth = normalize_code(cells[2])
    https = normalize_code(cells[3])
    cors = normalize_code(cells[4])
    row = Row(line_number, name, url, description, auth, https, cors)
    report.rows.append(row)

    problem = url_problem(url)
    if problem:
        add_issue(report, line_number, "{}: {}".format(name, problem))

    if not description:
        add_issue(report, line_number, "{}: Description is empty".format(name))
    elif len(description) > 100:
        add_issue(
            report,
            line_number,
            "{}: Description exceeds 100 characters (found {})".format(name, len(description)),
        )

    check_allowed(
        report,
        line_number,
        name,
        "Auth",
        auth,
        VALID_AUTH,
        "one of {}".format(", ".join(sorted(VALID_AUTH))),
    )
    check_allowed(report, line_number, name, "HTTPS", https, VALID_HTTPS, "Yes or No")
    check_allowed(
        report, line_number, name, "CORS", cors, VALID_CORS, "Yes, No, or Unknown"
    )

    expected = SELECTED_BY_NAME.get(name)
    if expected is None:
        return

    report.seen_selected.add(name)
    if name in report.selected:
        add_issue(report, line_number, "duplicate selected entry: {}".format(name))
    else:
        report.selected[name] = row

    for field_name, expected_value in (
        ("url", expected.url),
        ("auth", expected.auth),
        ("https", expected.https),
        ("cors", expected.cors),
    ):
        actual_value = getattr(row, field_name)
        if actual_value != expected_value:
            add_issue(
                report,
                line_number,
                "{}: {} mismatch: expected {}, found {}".format(
                    name,
                    FIELD_LABELS[field_name],
                    expected_value,
                    actual_value or "<empty>",
                ),
            )


def validate_file(path: Path) -> Report:
    report = Report()
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as exc:
        add_issue(report, None, "cannot read {}: {}".format(path, exc))
        return report

    heading_index = None
    for index, line in enumerate(lines):
        if line.strip() == CATEGORY_HEADING:
            heading_index = index
            break
    if heading_index is None:
        add_issue(report, None, "category heading {!r} not found".format(CATEGORY_HEADING))
        return report
    report.heading_line = heading_index + 1

    index = heading_index + 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        add_issue(report, report.heading_line, "table header not found after Vehicle heading")
        return report

    header_cells = split_table_row(lines[index])
    report.header_line = index + 1
    normalized = tuple(cell.strip().lower() for cell in header_cells)
    if len(header_cells) != 5 or normalized != EXPECTED_HEADERS:
        add_issue(
            report,
            report.header_line,
            "expected table header 'API | Description | Auth | HTTPS | CORS', found {!r}".format(
                lines[index].strip()
            ),
        )
        return report

    index += 1
    while index < len(lines) and not lines[index].strip():
        index += 1
    if index >= len(lines):
        add_issue(report, report.header_line, "table separator not found")
        return report

    separator_cells = split_table_row(lines[index])
    report.separator_line = index + 1
    if len(separator_cells) != 5:
        add_issue(
            report,
            report.separator_line,
            "expected 5 separator cells, found {}".format(len(separator_cells)),
        )
    else:
        for number, cell in enumerate(separator_cells, 1):
            if not re.fullmatch(r":?-{3,}:?", cell.strip()):
                add_issue(
                    report,
                    report.separator_line,
                    "separator column {} must look like ---, :---, ---: or :---:; found {!r}".format(
                        number, cell.strip()
                    ),
                )

    index += 1
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()
        if not stripped:
            break
        if stripped.startswith("**") or stripped.startswith("<") or stripped.startswith("#"):
            break
        validate_row(report, line, index + 1)
        report.table_end_line = index + 1
        index += 1

    if report.table_end_line is None:
        add_issue(report, report.separator_line, "Vehicle table has no data rows")

    for expected in SELECTED:
        if expected.name not in report.seen_selected:
            add_issue(report, None, "missing selected entry: {}".format(expected.name))

    return report


def display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT))
    except ValueError:
        return str(path)


def format_issue(path: str, issue: Issue) -> str:
    if issue.line is None:
        return "{}: {}".format(path, issue.message)
    return "{}:{}: {}".format(path, issue.line, issue.message)


def print_report(report: Report, path: Path) -> None:
    display = display_path(path)
    if report.heading_line is None:
        for issue in report.issues:
            print(format_issue(display, issue))
        print("FAIL: {} error(s)".format(len(report.issues)))
        return

    end_line = report.table_end_line or report.separator_line or report.heading_line
    print("{}: Vehicle table lines {}-{}".format(display, report.heading_line, end_line))
    print("Selected entries:")
    for expected in SELECTED:
        row = report.selected.get(expected.name)
        if row is None:
            print("  FAIL  {}: not found".format(expected.name))
            continue
        matches = (
            row.url == expected.url
            and row.auth == expected.auth
            and row.https == expected.https
            and row.cors == expected.cors
            and not any(issue.line == row.line for issue in report.issues)
        )
        print(
            "  {}  line {}: {} | Auth={} | HTTPS={} | CORS={}".format(
                "OK  " if matches else "FAIL",
                row.line,
                row.name,
                row.auth,
                row.https,
                row.cors,
            )
        )

    if report.issues:
        print("\nErrors:")
        for issue in report.issues:
            print("  {}".format(format_issue(display, issue)))
        print("\nFAIL: {} error(s)".format(len(report.issues)))
    else:
        print(
            "\nOK: Vehicle table structure valid; all {} selected entries match expected metadata.".format(
                len(SELECTED)
            )
        )


def compare_expected_row(row: Row, expected_row: Dict[str, object], problems: List[str]) -> None:
    for field_name in ("line", "url", "auth", "https", "cors"):
        if field_name in expected_row and getattr(row, field_name) != expected_row[field_name]:
            problems.append(
                "{}.{}: expected {!r}, got {!r}".format(
                    expected_row.get("name"),
                    field_name,
                    expected_row[field_name],
                    getattr(row, field_name),
                )
            )


def run_self_test() -> int:
    manifest_path = FIXTURES_DIR / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValueError) as exc:
        print("FAIL self-test: cannot read {}: {}".format(manifest_path, exc))
        return 2

    cases = manifest.get("cases")
    if not isinstance(cases, list) or not cases:
        print("FAIL self-test: manifest has no cases")
        return 2
    expected_exits = [case.get("expect_exit") for case in cases]
    if 0 not in expected_exits or not any(code != 0 for code in expected_exits):
        print("FAIL self-test: manifest must include passing and failing cases")
        return 1

    failures = 0
    for case in cases:
        filename = case.get("file")
        if not filename:
            print("FAIL self-test: case without a file")
            failures += 1
            continue
        path = FIXTURES_DIR / filename
        report = validate_file(path)
        actual_exit = 0 if report.ok else 1
        expected_exit = case.get("expect_exit")
        problems: List[str] = []

        if actual_exit != expected_exit:
            problems.append("expected exit {}, got {}".format(expected_exit, actual_exit))

        for field_name, expected_value in case.get("expected_table", {}).items():
            actual_value = getattr(report, field_name, None)
            if actual_value != expected_value:
                problems.append(
                    "{}: expected {!r}, got {!r}".format(field_name, expected_value, actual_value)
                )

        for expected_error in case.get("expected_errors", []):
            line = expected_error.get("line", "any")
            contains = expected_error.get("contains", "")
            matched = any(
                (line == "any" or issue.line == line) and contains in issue.message
                for issue in report.issues
            )
            if not matched:
                problems.append(
                    "missing expected error at line {}: {!r}".format(line, contains)
                )
        # Detect any unexpected validation errors not listed in expected_errors
        for issue in report.issues:
            if any(
                (exp_err.get("line", "any") == "any" or issue.line == exp_err.get("line", "any"))
                and exp_err.get("contains", "") in issue.message
                for exp_err in case.get("expected_errors", [])
            ):
                continue
            problems.append(f"unexpected error at line {issue.line}: {issue.message}")

        # Detect any unexpected validation errors that were not listed in expected_errors
        for issue in report.issues:
            # If this issue was already matched above, skip
            if any(
                (exp_err.get("line", "any") == "any" or issue.line == exp_err.get("line", "any"))
                and exp_err.get("contains", "") in issue.message
                for exp_err in case.get("expected_errors", [])
            ):
                continue
            problems.append(f"unexpected error at line {issue.line}: {issue.message}")


        for expected_row in case.get("expected_entries", []):
            row = report.selected.get(expected_row.get("name"))
            if row is None:
                problems.append(
                    "selected entry not parsed: {!r}".format(expected_row.get("name"))
                )
                continue
            compare_expected_row(row, expected_row, problems)

        rows_by_name = {row.name: row for row in report.rows}
        for expected_row in case.get("expected_rows", []):
            row = rows_by_name.get(expected_row.get("name"))
            if row is None:
                problems.append("row not parsed: {!r}".format(expected_row.get("name")))
                continue
            compare_expected_row(row, expected_row, problems)

        if problems:
            failures += 1
            print("FAIL {}".format(filename))
            for problem in problems:
                print("  - {}".format(problem))
            for issue in report.issues:
                print("    issue: {}".format(format_issue(display_path(path), issue)))
        else:
            print("PASS {}".format(filename))

    print("\nSelf-test: {}/{} fixtures passed".format(len(cases) - failures, len(cases)))
    return 0 if failures == 0 else 1


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate the R02-T036 entries in the README Vehicle table."
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="run the offline fixture suite from work/R02-T036/fixtures/",
    )
    parser.add_argument(
        "--readme",
        type=Path,
        default=DEFAULT_README,
        help="README file to validate (default: repository README.md)",
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    report = validate_file(args.readme)
    print_report(report, args.readme)
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
