# Course Checkers

## R02-T039 — Books section checker

### Purpose

`r02-t039.py` validates the **Books** table in `README.md` against the
formatting and contribution rules from `CONTRIBUTING.md`.

The three selected entries are:

| API | URL | Auth | HTTPS | CORS | README line |
|-----|-----|------|-------|------|-------------|
| A Bíblia Digital | https://www.abibliadigital.com.br/en | No* | Yes | No | 344 |
| Amanah Sunnah | https://sunnah.amanahagent.cloud/developers | `apiKey` | Yes | Yes | 345 |
| Bhagavad Gita | https://docs.bhagavadgitaapi.in | `apiKey` | Yes | Yes | 346 |

\* Historical documentation verification proves that unauthenticated requests were permitted (limited to 20 req/hr/IP; an optional free token increased the limit but was not mandatory), so historical Auth is `No`. The current README lists `` `apiKey` ``, which is reported as an evidence-backed discrepancy.

Pinned source commit: `2676ca49d557ef14a0f478311506dae947639028`

### Validation rules enforced

1. `### Books` heading present.
2. Exact table header: `API | Description | Auth | HTTPS | CORS |`
3. Exact separator: `|:---|:---|:---|:---|:---|`
4. Each data row has exactly five columns.
5. Exact one-space cell padding around each table delimiter.
6. Description length does not exceed 100 characters.
7. Name cell contains a valid Markdown link `[Name](URL)`.
8. Link URL is non-empty.
9. Auth is one of: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`.
10. HTTPS is `Yes` or `No`.
11. CORS is `Yes`, `No`, or `Unknown`.
12. Rows are alphabetically ordered (case-insensitive) within the section.
13. All three selected entries are present with expected metadata.
14. Selected entries are verified against their immediate preceding and following neighbors.

### Usage

```bash
python3 tools/course_checks/r02-t039.py --self-test   # offline fixture test suite (17 fixtures)
python3 tools/course_checks/r02-t039.py               # live README validation
python3 tools/course_checks/r02-t039.py --live        # live validation + sequential URL probe
python3 tools/course_checks/r02-t039.py --readme PATH # validate a custom README path
```

Exit code `0` = all checks pass. Exit code `1` = at least one error.

In live reporting:
- Task-specific selected APIs are validated and displayed with individual row status.
- Selected-entry internal ordering and neighbor ordering are explicitly checked.
- Section-wide errors remain cleanly separated from task-specific reporting.
- An optional `--live` flag performs sequential HTTP requests for the 3 documentation URLs using a 5-second timeout and no retries.
- Failed or unreachable HTTP probes are reported as `[UNVERIFIED / INCONCLUSIVE]`; automated request failures do not mark an entry as broken or cause exit code 1.

### Fixture coverage

Fixtures and manifest are in `work/R02-T039/fixtures/`.

| Fixture | Expected exit | Expected error codes | Description |
|---------|:-------------:|----------------------|-------------|
| `valid-all.md` | 0 | — | Valid table with all 3 selected entries and neighbor |
| `missing-entry.md` | 1 | `missing_entry` | Bhagavad Gita omitted from the table |
| `malformed-row.md` | 1 | `bad_link`, `missing_entry` | Missing closing bracket in Markdown link |
| `bad-link.md` | 1 | `empty_url`, `wrong_url` | Empty URL destination `[]()` |
| `invalid-auth.md` | 1 | `invalid_auth`, `wrong_auth` | Unsupported Auth value `Token` |
| `invalid-https.md` | 1 | `invalid_https`, `wrong_https` | Unsupported HTTPS value `Maybe` |
| `invalid-cors.md` | 1 | `invalid_cors`, `wrong_cors` | Unsupported CORS value `Maybe` |
| `wrong-order.md` | 1 | `wrong_order` | Alphabetical ordering violation among selected entries |
| `bad-columns.md` | 1 | `bad_column_count` | Row with 4 columns instead of 5 |
| `long-description.md` | 1 | `description_too_long` | Description exceeding 100 characters |
| `bad-padding.md` | 1 | `bad_padding` | Delimiter missing leading space |
| `non-english.md` | 0 | — | Valid non-English Unicode descriptions preserved |
| `paren-url.md` | 1 | `wrong_url` | URL containing balanced parentheses |
| `query-encoded.md` | 1 | `wrong_url` | URL containing query parameters and percent-encoding |
| `header-error.md` | 1 | `bad_header` | Incorrect column heading in table header |
| `separator-error.md` | 1 | `bad_separator` | Non-standard alignment in separator row |
| `neighbor-order-error.md` | 1 | `wrong_order` | Selected API placed after subsequent neighbor |

### API verification & documentation evidence

- **A Bíblia Digital** (`https://www.abibliadigital.com.br/en`):
  - **Historical Auth**: Official historical repository documentation shows unauthenticated requests were permitted (limited to 20 requests/hour/IP). An optional free token removed that limit but was not mandatory. Therefore, the historical Auth classification is `No`.
  - **Catalogue Discrepancy**: The upstream README lists `apiKey`, which the checker reports as an evidence-backed discrepancy on line 344 (`wrong_auth`). The root README is kept unchanged per instructions.
  - **Service Status**: Official GitHub repository records service and API shutdown on 2026-08-01.
- **Amanah Sunnah** (`https://sunnah.amanahagent.cloud/developers`): Developer portal requires `X-API-Key`, states keys are free, with no billing, usage caps, or rate limits. Catalogue entry matches `apiKey`.
- **Bhagavad Gita** (`https://docs.bhagavadgitaapi.in`): Domain currently displays a domain-for-sale placeholder. Access requirements are treated as unverified evidence; no alternative domain is substituted, and values are not invented. Catalogue consistency verifies the entry without conflating it with external reachability.

