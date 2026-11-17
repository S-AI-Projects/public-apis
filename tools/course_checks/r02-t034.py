"""Check category consistency for the R02-T034 assigned APIs."""

import sys
from collections import defaultdict
from pathlib import Path

README = Path(__file__).resolve().parents[2] / "README.md"

SELECTED = {
    "https://aidevboard.com/openapi.yaml": ("AI Dev Jobs", "Jobs"),
    "https://aitrainer.work/open-data#api": ("AI Trainer Work", "Jobs"),
    "https://developer.adzuna.com/overview": ("Adzuna", "Jobs"),
}


def scan(lines):
    categories = defaultdict(list)
    entries = {}
    current = None
    in_catalogue = False

    for number, line in enumerate(lines, 1):
        if line.strip() == "## Index":
            in_catalogue = True
            continue
        if line.startswith("## ") and in_catalogue:
            break
        if not in_catalogue:
            continue

        if line.startswith("### "):
            current = line[4:].strip()
            categories[current].append(number)

        elif current and line.startswith("|"):
            for url, (name, _) in SELECTED.items():
                if url in line:
                    entries[url] = (name, current, number)

    return categories, entries


def check(lines):
    categories, entries = scan(lines)
    errors = []

    for url, (name, expected) in SELECTED.items():
        if url not in entries:
            errors.append(f"Missing: {name} ({url})")
            continue

        _, actual, line = entries[url]
        if actual != expected:
            errors.append(
                f"Misplaced: {name}, category={actual}, "
                f"expected={expected}, line={line}"
            )

    for name, numbers in categories.items():
        if len(numbers) > 1:
            errors.append(f"Repeated heading: {name}, lines={numbers}")

    return errors, entries


def self_test():
    fixtures = Path(__file__).resolve().parents[2] / "work/R02-T034/fixtures"

    def load(name):
        return (fixtures / name).read_text(encoding="utf-8").splitlines()

    errors, entries = check(load("valid.md"))
    if errors or len(entries) != 3:
        raise RuntimeError("Valid fixture failed")

    errors, _ = check(load("misplaced.md"))
    if sum("Misplaced:" in error for error in errors) != 3:
        raise RuntimeError("Misplaced-entry test failed")

    errors, _ = check(load("repeated-heading.md"))
    if not any("Repeated heading: Jobs" in error for error in errors):
        raise RuntimeError("Repeated-heading test failed")

    errors, _ = check(load("missing-entry.md"))
    if not any("Missing: Adzuna" in error for error in errors):
        raise RuntimeError("Missing-entry test failed")

    print("Self-test passed: 4 fixture checks")


def main():
    if "--self-test" in sys.argv:
        self_test()
        return

    errors, entries = check(README.read_text(encoding="utf-8").splitlines())

    for _, (name, category, line) in entries.items():
        print(f"{name}: {category} (line {line})")

    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        sys.exit(1)

    print("Category consistency check passed.")


if __name__ == "__main__":
    main()
