# Course Checkers

## R02-T031 — Parse the entries: Social [README.md]

### Purpose

`r02-t031.py` is an offline checker that parses the `Social` section of the
repository `README.md` and extracts three assigned API entries together with
their original source line numbers.

It is a read-only verification tool. It never modifies `README.md` and never
makes network requests.

### Usage

```bash
# Run the offline self-test (writes work/R02-T031/actual.json)
python3 tools/course_checks/r02-t031.py --self-test

# Extract the assigned entries from the real README
python3 tools/course_checks/r02-t031.py

# Extract from an explicit Markdown file
python3 tools/course_checks/r02-t031.py --input path/to/file.md
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
  active category is no longer `Social`.
- Markdown fenced code blocks are skipped. Both backtick (`` ``` ``) and tilde
  (`~~~`) fences are recognised, including fences with an info string such as
  `` ```markdown ``. A closing fence must use the same character and be at
  least as long as the opening fence.
- Table header rows must begin with `api` or `name` and contain a `description`
  column, matching the actual `Social` table schema in `README.md`.
- Table separators (`|---|---|`) and rows whose cell count does not match the
  header are ignored.
- Only the three assigned display names are extracted, and only while the
  active category is exactly `Social`.
- URL fragments (for example `#overview`) are preserved verbatim.
- Parsing uses Python's standard library only (`argparse`, `json`, `re`,
  `subprocess`, `sys`, `pathlib`).

### Output fields

Each extracted entry is an object with:

| Field | Description |
|-------|-------------|
| `display_name` | Link text of the API name. |
| `url` | Full URL, including any fragment. |
| `category` | Active category heading — always `Social` here. |
| `source_line` | 1-based line number of the row in the parsed input file. |
| `metadata` | Map of remaining table columns (for example `description`, `auth`, `https`, `cors`), with inline code delimiters stripped. |

### Assigned entries

These are the three entries extracted from the pinned `README.md`
(`2676ca49`), all inside the `Social` section:

| # | Display name | URL | README line |
|---|--------------|-----|-------------|
| 1 | 4chan | `https://github.com/4chan/4chan-API` | 2289 |
| 2 | API Direct | `https://apidirect.io/docs` | 2290 |
| 3 | Ayrshare | `https://www.ayrshare.com` | 2291 |

The `Social` section spans lines 2286–2351 (the next `###` heading,
`### Sports & Fitness`, is at line 2352).

### Offline fixtures and self-test

Fixtures live in `work/R02-T031/fixtures/`:

- `input.md` — success cases (the three assigned entries, with a URL fragment
  and exact source lines 7/8/9) plus failure cases that must **not** be
  extracted:
  - a non-assigned Social entry (`Blogger`),
  - a wrong-category entry inside a `### Development` section,
  - a backtick-fenced table containing a target name and a fake link,
  - a tilde-fenced table containing two target names.
  All fences in this fixture are balanced and each failure case sits outside
  or inside the correct fence, so the cases are genuinely exercised.
- `expected.json` — the exact expected extraction result for `input.md`.
- `no-match.md` — a failure input containing no assigned entry at all; the
  checker must return nothing and exit non-zero.

`--self-test` runs `extract_entries` against `input.md`, compares the result
to `expected.json`, checks each success and failure case explicitly, verifies
the no-match input, and confirms that a no-match input makes the CLI exit
non-zero. It writes the observed result to `work/R02-T031/actual.json`.

### Evidence

Inputs, expected and actual results, tool versions and formatter output are
recorded under `work/R02-T031/`.
