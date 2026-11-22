# Course Checkers

## R02-T040 — Patent section checker

### Purpose

`r02-t040.py` validates the **Patent** table in `README.md` against the
formatting and contribution rules specified in `CONTRIBUTING.md`.

The three assigned entries are:

| API | URL | Auth | HTTPS | CORS | README Line (Dynamic) |
|-----|-----|------|-------|------|:---------------------:|
| EPO | https://developers.epo.org/ | `OAuth` | Yes | Unknown | 1994 |
| PatentsView | https://patentsview.org/apis/purpose | No | Yes | Unknown | 1995 |
| TIPO | https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00 | `apiKey` | Yes | Unknown | 1996 |

Pinned source commit: `2676ca49d557ef14a0f478311506dae947639028`

### Validation rules enforced

1. `### Patent` section heading present.
2. Exact table header: `API | Description | Auth | HTTPS | CORS |`
3. Exact table separator: `|:---|:---|:---|:---|:---|`
4. Exactly five columns per data row.
5. Exact one-space padding around all Markdown table delimiters (`| cell |`), rejecting both missing spaces and multiple spaces.
6. Description length does not exceed 100 characters.
7. Name cell contains a valid Markdown link `[Name](URL)`.
8. Link destination URL is non-empty.
9. Allowed Auth values: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`.
10. Allowed HTTPS values: `Yes`, `No`.
11. Allowed CORS values: `Yes`, `No`, `Unknown`.
12. Rows are alphabetically ordered (case-insensitive) within the section.
13. Selected entries are verified against expected metadata.
14. Selected entries are validated against their immediate preceding and following neighbors.
15. Dynamic 1-based source line numbers are resolved and reported without hardcoding.

### Usage

```bash
# Run offline fixture self-test suite (20 fixtures)
python3 tools/course_checks/r02-t040.py --self-test

# Run live validation against repository README.md
python3 tools/course_checks/r02-t040.py

# Run validation and execute sequential live HTTP probes
python3 tools/course_checks/r02-t040.py --live

# Validate a custom input file or fixture
python3 tools/course_checks/r02-t040.py --readme PATH
```

Exit code `0` = all validation checks pass. Exit code `1` = one or more errors detected.

### Report Structure

`r02-t040.py` generates a deterministic report structured into distinct sections:
- **[1. SOURCE FACTS & SCOPE]**: Dynamic 1-based line locations, target file, heading, and row counts.
- **[2. EXISTING CATALOGUE METADATA]**: Raw values and dynamic lines from the file.
- **[3. OFFICIAL DOCUMENTATION OBSERVATIONS]**: Exact source URLs and verified technical observations.
- **[4. HISTORICAL INFORMATION & VERSION DISTINCTIONS]**: Version context and migration facts.
- **[5. MANUAL DECISIONS & RECOMMENDED METADATA]**: Actionable rationale for each entry.
- **[6. UNVERIFIED OR INCONCLUSIVE INFORMATION]**: Inconclusive observations explicitly separated from confirmed errors.
- **[7. SECTION-WIDE & NEIGHBOR STRUCTURAL VALIDATION]**: Table delimiters, padding, ordering, and length.
- **[8. AUTOMATED VALIDATION SUMMARY]**: Task-specific and section-wide pass/fail outcomes.
- **[9. LIVE DOCUMENTATION PROBE]** (Optional, `--live`): Sequential probes with a 5-second timeout, low concurrency, and no retries.

### Fixture coverage

Fixtures and manifest are located in `work/R02-T040/fixtures/`.

| Fixture | Expected exit | Expected error codes | Description |
|---------|:-------------:|----------------------|-------------|
| `valid-all.md` | 0 | — | Valid table with all 3 selected entries and neighbor |
| `missing-entry.md` | 1 | `missing_entry` | TIPO entry omitted from table |
| `malformed-row.md` | 1 | `bad_link`, `missing_entry` | Missing closing bracket in Markdown link |
| `bad-link.md` | 1 | `empty_url`, `wrong_url` | Empty URL destination `[]()` |
| `invalid-auth.md` | 1 | `invalid_auth`, `wrong_auth` | Unsupported Auth value `Token` |
| `invalid-https.md` | 1 | `invalid_https`, `wrong_https` | Unsupported HTTPS value `Maybe` |
| `invalid-cors.md` | 1 | `invalid_cors`, `wrong_cors` | Unsupported CORS value `Maybe` |
| `wrong-order.md` | 1 | `wrong_order` | Alphabetical ordering violation |
| `bad-columns.md` | 1 | `bad_column_count` | Row with 4 columns instead of 5 |
| `long-description.md` | 1 | `description_too_long` | Description exceeding 100 characters |
| `bad-padding.md` | 1 | `bad_padding` | Delimiter missing leading space |
| `multiple-spaces-padding.md` | 1 | `bad_padding` | Delimiter with multiple spaces |
| `missing-heading.md` | 1 | `missing_heading` | Section heading `### Patent` missing |
| `header-error.md` | 1 | `bad_header` | Incorrect column heading in table header |
| `separator-error.md` | 1 | `bad_separator` | Non-standard alignment in separator row |
| `metadata-discrepancy.md` | 1 | `wrong_auth` | Unexpected Auth value on selected entry |
| `unverified-info.md` | 0 | — | Unverified external evidence does not trigger errors |
| `neighbor-order-error.md` | 1 | `wrong_order` | Selected entry placed after subsequent neighbor |
| `dynamic-line-numbers.md` | 0 | — | Extra preamble lines test dynamic line number resolution |
| `non-english.md` | 0 | — | Valid Traditional Chinese Unicode preserved |

### Summary of Manual Verification & Evidence

- **EPO** (`https://developers.epo.org/`):
  - Open Patent Services (OPS) v3.2 uses OAuth 2.0 client credentials (`OAuth`).
  - Served over HTTPS; CORS is undocumented (`Unknown`).
  - Decision: Existing catalogue metadata is correct. Retain as-is.
- **PatentsView** (`https://patentsview.org/apis/purpose`):
  - Legacy API at assigned URL was an open, unauthenticated REST API (`No`).
  - Current PatentSearch API requires registration and an `X-Api-Key` header (`apiKey`).
  - Migration to the USPTO Open Data Portal (`data.uspto.gov` / `api.uspto.gov`) is underway.
  - Decision: Preserve existing `No` in README to avoid conflating the legacy API entry with the new PatentSearch API. Root README is kept unchanged per policy.
- **TIPO** (`https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00`):
  - Taiwan Intellectual Property Office Gazette Open Data service (API00) uses account/password authentication to obtain an API access token (Bearer token).
  - Under `CONTRIBUTING.md`, private token/key authentication is classified as `apiKey`.
  - HTTPS is supported; CORS is undocumented (`Unknown`).
  - Decision: Retain `apiKey` as the proper classification under contribution guidelines.
