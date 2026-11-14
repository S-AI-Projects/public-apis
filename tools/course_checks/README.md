# Coursework Checks — R02-T028: Check the list's formatting — News (README.md)

This directory contains deterministic offline verification checkers, list formatting rules, and test fixtures for coursework task R02-T028.

---

## 1. Task Purpose & Selected Entries

The purpose of this check is to validate the formatting, Markdown table syntax, heading hierarchy, and documented ordering rules for the **News** category in `README.md`, scoped to the three assigned entries:

| API Name | Source Line | URL | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|:---|
| **Mediastack** | Line 1854 | `https://mediastack.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers` | `apiKey` | Yes | Unknown |
| **Associated Press** | Line 1855 | `https://developer.ap.org/` | `apiKey` | Yes | Unknown |
| **Chronicling America** | Line 1856 | `http://chroniclingamerica.loc.gov/about/api/` | No | Yes | Unknown |

Category Section Header: `### News` (Line 1851)

---

## 2. Formatting & Syntax Rules Verified

The checker enforces the repository's contribution standards from `CONTRIBUTING.md` and `scripts/validate/format.py`:

1. **Heading Hierarchy & Boundaries:**
   - Categories must use an H3 heading: `### CategoryName`.
   - Table starts immediately after the category heading with a 5-column header and alignment delimiter.
   - Category scope terminates at the next category heading or `**[⬆ Back to Index](#index)**`.

2. **Table Syntax & Columns:**
   - Each entry row must contain exactly 5 columns separated by `|`:
     - Column 1: API Title link `[Name](URL)`.
     - Column 2: Description.
     - Column 3: Authentication requirement.
     - Column 4: HTTPS support (`Yes` / `No`).
     - Column 5: CORS support (`Yes` / `No` / `Unknown`).
   - Rows with fewer or more than 5 columns are detected as malformed entries and reported with their source line numbers.

3. **Title and Markdown Link Rules:**
   - Link syntax must follow `[Title](URL)`.
   - Balanced parentheses within URLs (e.g. `(balanced)`) and query strings (`?utm_...`) are preserved without corruption or normalization.
   - API titles must not end with redundant `... API`.

4. **Description Rules:**
   - First character must be capitalized.
   - Description length must not exceed 100 characters.
   - Trailing punctuation (`.`, `-`, `,`) is prohibited.

5. **Metadata Vocabulary:**
   - `Auth`: Must be one of `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`. Values other than `No` must be enclosed in backticks (e.g. `` `apiKey` ``).
   - `HTTPS`: Must be `Yes` or `No`.
   - `CORS`: Must be `Yes`, `No`, or `Unknown`.

6. **Alphabetical Ordering Rules:**
   - Entries within a section must be ordered alphabetically by title (case-insensitive: `title.upper()`).
   - The checker detects any entry appearing out of alphabetical order, detects every adjacent ordering inversion, includes `expected_sorted_order` in the JSON report, and records specific offending lines under `ordering_issues`.

---

## 3. Offline Fixture Coverage

Fixtures are located under `tools/course_checks/fixtures/r02-t028/`:

1. `valid_entries.md`: Positive baseline of valid table syntax, H3 heading, and alphabetical ordering.
2. `malformed_entry.md`: Table row containing 3 columns instead of 5, rejected with line number reporting (line 5).
3. `missing_required_field.md`: Table row missing the description field, rejected as invalid.
4. `incorrect_ordering.json`: Tests the exact three-entry ordering inversion case (`Mediastack` appearing before `Associated Press`) with expected sorted order and inversions.
5. `incorrect_ordering.md`: Markdown input corresponding to the out-of-order scenario.
6. `invalid_heading_hierarchy.md`: Category heading using `## News` instead of `### News`, rejected by heading hierarchy validation.
7. `duplicate_entry.md`: Duplicate entry rows for `Mediastack`, detected and flagged in duplicate list.
8. `valid_non_english.md`: Entries with Unicode/non-English characters (`Michał`, `São Paulo`, `München`), preserved exactly without escaping.
9. `url_query_parameters.md`: Markdown links containing query strings (`?utm_source=...&access_key=...`), preserved exactly.
10. `source_line_tracking.md`: Verifies line tracking accuracy with preambles and offsets.
11. `outside_category.md`: Verifies that entries outside the `News` category (e.g. under `### Animals` or `### Sports`) are ignored.

---

## 4. Usage & Validation Commands

### Run Deterministic Offline Self-Tests
```bash
python3 tools/course_checks/r02-t028.py --self-test
```

### Run Normal Formatting Check Against README.md
```bash
python3 tools/course_checks/r02-t028.py
```

### Python Bytecode Compilation Check
```bash
python3 -m py_compile tools/course_checks/r02-t028.py
```

### Git Whitespace Check
```bash
git diff --check
```
