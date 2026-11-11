from pathlib import Path
import argparse
import re
from pathlib import Path
import argparse
import re


# Project paths
BASE_DIR = Path(__file__).resolve().parents[2]

README_PATH = BASE_DIR / "README.md"

FIXTURE_DIR = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "r02-t021"
)

FIXTURE_PATH = FIXTURE_DIR / "currency_exchange.md"

MISSING_CATEGORY_FIXTURE_PATH = (
    FIXTURE_DIR / "missing_category.md"
)


# Task configuration
CATEGORY = "Currency Exchange"

SELECTED_APIS = {
    "Currencylayer",
    "Exchangerate.host",
    "Exchangeratesapi.io",
}


def parse_markdown_row(line: str) -> dict | None:
    """Parse one Markdown API table row."""

    line = line.strip()

    if not line.startswith("|"):
        return None

    cells = [
        cell.strip()
        for cell in line.strip("|").split("|")
    ]

    if len(cells) != 5:
        return None

    link_match = re.fullmatch(
        r"\[([^\]]+)\]\((.+)\)",
        cells[0],
    )

    if not link_match:
        return None

    return {
        "name": link_match.group(1),
        "url": link_match.group(2),
        "description": cells[1],
        "auth": cells[2].strip("`"),
        "https": cells[3],
        "cors": cells[4],
    }


def extract_entries(readme_text: str) -> list[dict]:
    """Extract selected APIs from the target category."""

    lines = readme_text.splitlines()

    heading = f"### {CATEGORY}"

    start = None

    for index, line in enumerate(lines):
        if line.strip() == heading:
            start = index + 1
            break

    if start is None:
        raise ValueError(f"Category not found: {CATEGORY}")

    entries = []
    inside_code_block = False
    fence_marker = None
    fence_length = 0

    for index in range(start, len(lines)):
        line = lines[index]
        stripped = line.strip()

        # Detect fenced code blocks.
        fence_match = re.match(r"^(`{3,}|~{3,})", stripped)

        if fence_match:
            marker = fence_match.group(1)

            if not inside_code_block:
                inside_code_block = True
                fence_marker = marker[0]
                fence_length = len(marker)

            elif (
                marker[0] == fence_marker
                and len(marker) >= fence_length
            ):
                inside_code_block = False
                fence_marker = None
                fence_length = 0

            continue

        # Ignore content inside code blocks.
        if inside_code_block:
            continue

        # Stop when the next category begins.
        if stripped.startswith("### "):
            break

        parsed = parse_markdown_row(line)

        if parsed and parsed["name"] in SELECTED_APIS:
            parsed["category"] = CATEGORY
            parsed["line_number"] = index + 1

            entries.append(parsed)

    return entries


def run_self_tests() -> None:
    """Run offline tests using local fixture files."""

    # Test successful parsing.
    fixture = FIXTURE_PATH.read_text(encoding="utf-8")

    entries = extract_entries(fixture)

    assert len(entries) == 3, (
        f"Expected 3 entries, got {len(entries)}"
    )

    assert [
        entry["name"] for entry in entries
    ] == [
        "Currencylayer",
        "Exchangerate.host",
        "Exchangeratesapi.io",
    ]

    # Verify original line numbers.
    assert entries[0]["line_number"] == 6
    assert entries[1]["line_number"] == 10
    assert entries[2]["line_number"] == 11

    # Verify URL fragments are preserved.
    assert (
        entries[0]["url"]
        == "https://example.com/rates#latest"
    )

    assert (
        entries[1]["url"]
        == "https://real.example#current"
    )

    # Verify category metadata.
    assert all(
        entry["category"] == CATEGORY
        for entry in entries
    )

    # Verify code-block entry was ignored.
    assert all(
        entry["url"] != "https://fake.example"
        for entry in entries
    )

    # Test missing-category failure.
    missing_fixture = (
        MISSING_CATEGORY_FIXTURE_PATH.read_text(
            encoding="utf-8"
        )
    )

    try:
        extract_entries(missing_fixture)

    except ValueError:
        pass

    else:
        raise AssertionError(
            "Expected ValueError for missing category"
        )

    # Test malformed Markdown row.
    malformed_row = "| Invalid entry | Missing URL |"

    assert parse_markdown_row(malformed_row) is None

    print("All offline tests passed!")


def main() -> None:
    """Handle command-line execution."""

    parser = argparse.ArgumentParser(
        description=(
            "Parse selected Currency Exchange API entries."
        )
    )

    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Run offline parser tests.",
    )

    args = parser.parse_args()

    if args.self_test:
        run_self_tests()
        return

    readme_text = README_PATH.read_text(
        encoding="utf-8"
    )

    entries = extract_entries(readme_text)

    for entry in entries:
        print(entry)


if __name__ == "__main__":
    main()
