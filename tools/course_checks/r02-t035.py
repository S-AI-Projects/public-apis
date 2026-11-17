"""Check the R02-T035 News entries and their required metadata."""

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
README = ROOT / "README.md"
FIXTURES = ROOT / "work/R02-T035/fixtures"

COLUMNS = ("API", "Description", "Auth", "HTTPS", "CORS")
AUTH_VALUES = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
HTTPS_VALUES = {"Yes", "No"}
CORS_VALUES = {"Yes", "No", "Unknown"}
EXPECTED = {
    "Mediastack": ("apiKey", "Yes", "Yes"),
    "Associated Press": ("apiKey", "Yes", "Unknown"),
    "Chronicling America": ("No", "Yes", "Unknown"),
}
LINK = re.compile(r"\[([^\]]+)\]\([^)]*\)")


def news_rows(lines):
    """Return the News table header and rows with their original line numbers."""
    start = next(
        (number for number, line in enumerate(lines, 1) if line.strip() == "### News"),
        None,
    )
    if start is None:
        return None, []

    header = None
    rows = []
    for number, line in enumerate(lines[start:], start + 1):
        text = line.strip()
        if not text:
            if rows:
                break
            continue
        if text.startswith("### ") or text.startswith("## "):
            break
        cells = [cell.strip() for cell in text.strip("|").split("|")]
        if header is None:
            header = (number, cells)
        elif not all(re.fullmatch(r":?-+:?", cell) for cell in cells):
            rows.append((number, cells))
    return header, rows


def check(lines):
    header, rows = news_rows(lines)
    if header is None:
        return ["Missing News section or table"], {}

    errors = []
    number, cells = header
    if tuple(cells) != COLUMNS:
        errors.append(f"Invalid News header at line {number}: {cells}")

    found = {}
    for number, cells in rows:
        match = LINK.search(cells[0])
        name = match.group(1) if match else cells[0]
        if name not in EXPECTED:
            continue

        found[name] = number
        if len(cells) != len(COLUMNS):
            errors.append(
                f"Missing required metadata: {name} has {len(cells)} of "
                f"{len(COLUMNS)} columns at line {number}"
            )
            continue

        fields = ("Auth", "HTTPS", "CORS")
        allowed = (AUTH_VALUES, HTTPS_VALUES, CORS_VALUES)
        for field, value, valid, expected in zip(
            fields, cells[2:], allowed, EXPECTED[name]
        ):
            value = value.strip("`")
            if not value:
                errors.append(
                    f"Missing required metadata: {name} {field} at line {number}"
                )
            elif value not in valid:
                errors.append(f"Invalid {field}: {name}={value!r} at line {number}")
            elif value != expected:
                errors.append(
                    f"Wrong {field}: {name}={value!r}, expected={expected!r} "
                    f"at line {number}"
                )

    for name in EXPECTED:
        if name not in found:
            errors.append(f"Missing entry: {name} in News")
    return errors, found


def exit_code(lines):
    return 1 if check(lines)[0] else 0


def self_test():
    cases = (
        ("valid.md", []),
        ("missing-field.md", ["Missing required metadata: Mediastack Auth at line 4"]),
        ("missing-entry.md", ["Missing entry: Associated Press in News"]),
        ("invalid-value.md", ["Invalid CORS: Associated Press='Sometimes' at line 5"]),
    )
    for filename, expected in cases:
        lines = (FIXTURES / filename).read_text(encoding="utf-8").splitlines()
        errors, _ = check(lines)
        if errors != expected:
            raise SystemExit(f"Self-test failed: {filename}: {errors}")
        if exit_code(lines) != (1 if expected else 0):
            raise SystemExit(f"Self-test exit-code failed: {filename}")
    print(f"Self-test passed: {len(cases)} fixture checks")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return

    errors, found = check(README.read_text(encoding="utf-8").splitlines())
    for name, number in found.items():
        print(f"{name}: News (line {number})")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        raise SystemExit(1)
    print("R02-T035 News metadata check passed.")


if __name__ == "__main__":
    main()
