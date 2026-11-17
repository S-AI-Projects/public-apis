# R02-T038 — Science & Math Section Checker

## Task summary

Validate three selected entries in the `Science & Math` section of the
`public-apis` README using a Python standard-library-only checker.

## Selected entries

| API | URL | Auth | HTTPS | CORS | README line |
|-----|-----|------|-------|------|-------------|
| arcsecond.io | https://api.arcsecond.io/ | No | Yes | Unknown | 2113 |
| arXiv | https://info.arxiv.org/help/api/user-manual.html | No | Yes | Unknown | 2114 |
| Botlero | https://botlero.com/api/robots | No | Yes | Yes | 2115 |

Pinned source commit: `2676ca49d557ef14a0f478311506dae947639028`

## Contribution rules discovered

From `CONTRIBUTING.md`:

- **Auth** allowed values: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`
- **CORS** allowed values: `Yes`, `No`, `Unknown`
- **HTTPS** allowed values: `Yes`, `No`
- **Ordering**: alphabetical per section (case-insensitive)
- **Description**: must not exceed 100 characters
- **Column padding**: one space on each side
- **Header format**: `API | Description | Auth | HTTPS | CORS |`
- **Separator format**: `|:---|:---|:---|:---|:---|`

## API verification

### arcsecond.io

- Official documentation: https://api.arcsecond.io/
- Description: Multiple astronomy data sources
- Auth: No authentication required for read endpoints
- HTTPS: Yes (served over HTTPS)
- CORS: Not documented; `Unknown` is correct
- README entry: **correct as-is** (line 2113)

### arXiv

- Official documentation: https://info.arxiv.org/help/api/user-manual.html
- Description: Curated research-sharing platform for physics, math, etc.
- Auth: No API key required (open access)
- HTTPS: Yes
- CORS: Not documented for the API; `Unknown` is correct
- README entry: **correct as-is** (line 2114)

### Botlero

- Official documentation: https://botlero.com/api/robots
- Description: Sourced, quoted specs for humanoid robots
- Auth: No authentication required
- HTTPS: Yes
- CORS: Documented as supported; `Yes` is correct
- README entry: **correct as-is** (line 2115)

### Relative ordering & neighbor validation of selected entries

- `arcsecond.io` (casefold: `arcsecond.io`): preceding neighbor = none (first entry in table), following neighbor = `arXiv`
- `arXiv` (casefold: `arxiv`): preceding neighbor = `arcsecond.io`, following neighbor = `Botlero`
- `Botlero` (casefold: `botlero`): preceding neighbor = `arXiv`, following neighbor = `Chempirical`
- Followed by `Chempirical` (line 2116, casefold: `chempirical`)

Comparison:
`"arcsecond.io" < "arxiv" < "botlero" < "chempirical"`

All three selected entries are at the beginning of the table and are strictly
in correct alphabetical order among themselves and relative to their immediate
preceding and following neighbors (including `Chempirical` after `Botlero`).
The checker explicitly checks neighbor ordering; any out-of-order neighbor
relationship marks the offending selected row as `[ERROR]` rather than `[OK]`.

## Upstream ordering violations investigation

Running live validation against `README.md` at pinned commit `2676ca49` detects
two ordering violations in the `Science & Math` section:

1. **Line 2140 (`NASA InSight` before `NASA ADS`)**:
   - Line 2139: `NASA InSight`
   - Line 2140: `NASA ADS`
   - Both entries begin with `NASA `. Comparing the next character:
     `I` (ASCII 73) > `A` (ASCII 65).
   - Alphabetically, `NASA ADS` must precede `NASA InSight`.
   - Git blame confirms `NASA InSight` was committed on 2026-08-25 (`e4de5dca6`),
     placed before `NASA ADS` (from 2021). This is a pre-existing upstream bug.

2. **Line 2151 (`OpenAlex` before `Open Ephemeris`)**:
   - Line 2150: `OpenAlex`
   - Line 2151: `Open Ephemeris`
   - At character index 4: `OpenAlex` has `A` (ASCII 65 / `a` 97), whereas
     `Open Ephemeris` has space ` ` (ASCII 32).
   - Under standard ASCII / Unicode collation (and uppercase/casefold):
     space precedes letters (`32 < 65`), so `Open Ephemeris` precedes `OpenAlex`.
   - Git blame confirms `Open Ephemeris` was added on 2026-09-14 (`26d3a2e77`),
     placed after `OpenAlex` (from 2026-05). This is also a pre-existing upstream bug.

3. **Confirmation from upstream tooling**:
   - Running the repository's own format checker:
     `python3 scripts/validate/format.py README.md`
   - Produces:
     `(L2110) Science & Math category is not alphabetical order`
   - Upstream's own script flags these identical issues.

## Reporting & exit code decision

- **Task-specific validation**: The checker explicitly validates the three
  coursework-assigned APIs and reports that they are all present, have valid
  syntax and metadata, and are correctly ordered relative to their neighbors.
- **Section-wide validation**: The checker also reports section-wide issues
  such as the two pre-existing ordering violations at lines 2140 and 2151.
- **Live exit code**: Because the upstream section contains genuine ordering
  errors, live validation exits with code `1`. The checker does NOT silently
  suppress or ignore these errors.
- **No changes to unrelated entries**: In accordance with coursework constraints
  ("Do not change unrelated API entries or silently suppress errors"), `README.md`
  is left unchanged.

## Checker implementation notes

- Parser uses a character-state machine to handle balanced parentheses in
  URLs and escaped pipes in table cells.
- Validates heading, exact header, exact separator, 5 columns per row,
  table delimiter cell padding, description length <= 100 chars,
  metadata values against allowed sets, and alphabetical order.
- Self-test loads `work/R02-T038/fixtures/manifest.json` and runs all 15
  fixtures offline (no network required).
- Unexpected-error detection: if the parser emits any error code not listed in
  `expected_errors`, or if error counts mismatch, the self-test fails.
