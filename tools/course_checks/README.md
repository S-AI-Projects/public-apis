# Course Checkers

## R02-T041 — Parse the entries: Calendar [README.md]

### Purpose

`r02-t041.py` is an offline checker that parses the `Calendar` section of the
repository `README.md` and extracts three assigned API entries together with
their original source line numbers.

It is a read-only verification tool. It never modifies `README.md` and never
makes network requests.

### Usage

```bash
# Run the offline self-test (writes work/R02-T041/actual.json)
python3 tools/course_checks/r02-t041.py --self-test

# Extract the assigned entries from the real README
python3 tools/course_checks/r02-t041.py

# Extract from an explicit Markdown file
python3 tools/course_checks/r02-t041.py --input path/to/file.md
```

Exit codes:

| Code | Meaning |
|------|---------|
| `0` | Success — the self-test passed, or at least one assigned entry was found. |
| `1` | Failure — an assertion failed, no assigned entry was found, or the input could not be read. |

Running with `python3 -O` (or `-OO`) disables `assert` statements. The checker
detects this and exits `1` rather than reporting a false pass.

### Parser behaviour

- Only `###` (level-3) headings are treated as category headings; any other
  heading level clears the active category. Extraction stops as soon as the
  active category is no longer `Calendar`.
- Markdown fenced code blocks are skipped. Both backtick (`` ``` ``) and tilde
  (`~~~`) fences are recognised, including fences with an info string such as
  `` ```markdown ``. A closing fence must use the same character and be at
  least as long as the opening fence.
- Table header rows must begin with `api` or `name` and contain a `description`
  column, matching the actual `Calendar` table schema in `README.md`.
- Table separators (`|---|---|` or `|:---|:---|`) and rows whose cell count does
  not match the header are ignored.
- Only the three assigned display names are extracted, and only while the
  active category is exactly `Calendar`.
- URL fragments (for example `#test-frag`) are preserved verbatim.
- Parsing uses Python's standard library only (`argparse`, `json`, `os`, `re`,
  `sys`, `pathlib`).

### Output fields

Each extracted entry is an object with:

| Field | Description |
|-------|-------------|
| `display_name` | Link text of the API name. |
| `url` | Full URL, including any fragment. |
| `category` | Active category heading — always `Calendar` here. |
| `source_line` | 1-based line number of the row in the parsed input file. |
| `metadata` | Map of remaining table columns (for example `description`, `auth`, `https`, `cors`), with inline code delimiters stripped. |

### Assigned entries

These are the three entries extracted from the pinned `README.md`
(`2676ca49`), all inside the `Calendar` section:

| # | Display name | URL | README line |
|---|--------------|-----|-------------|
| 1 | Africa Compliance Data | `https://africacompliancedata.com/docs` | 433 |
| 2 | caldays | `https://caldays.com/api` | 434 |
| 3 | Calendarific | `https://calendarific.com/` | 435 |

The `Calendar` section spans lines 430–454 (the next `###` heading,
`### Cloud Storage & File Sharing`, is at line 455).

### Offline fixtures and self-test

Fixtures live in `work/R02-T041/fixtures/`:

- `input.md` — success cases (the three assigned entries, with a URL fragment
  and exact source lines 7/8/9) plus failure cases that must **not** be
  extracted:
  - a non-assigned Calendar entry (`Checkiday - National Holiday`),
  - a wrong-category entry inside a `### Books` section,
  - a backtick-fenced table containing a target name and a fake link,
  - a tilde-fenced table containing two target names.
  All fences in this fixture are balanced and each failure case sits outside
  or inside the correct fence, so the cases are genuinely exercised.
- `expected.json` — the exact expected extraction result for `input.md`.
- `no-match.md` — a failure input containing no assigned entry at all; the
  checker must return nothing and exit non-zero.

`--self-test` runs `parse_markdown_entries` against `input.md`, compares the result
to `expected.json`, checks each success and failure case explicitly, verifies
the no-match input, and confirms that a no-match input makes the CLI exit
non-zero. It writes the observed result to `work/R02-T041/actual.json`.

### Evidence

Inputs, expected and actual results, tool versions and verification output are
recorded under `work/R02-T041/`.
