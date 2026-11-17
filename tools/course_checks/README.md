# Course Checkers

## R02-T038 — Science & Math section checker

### Purpose

`r02-t038.py` validates the **Science & Math** table in `README.md` against
the formatting and contribution rules from `CONTRIBUTING.md`.

The three selected entries are:

| API | URL | Auth | HTTPS | CORS | README line |
|-----|-----|------|-------|------|-------------|
| arcsecond.io | https://api.arcsecond.io/ | No | Yes | Unknown | 2113 |
| arXiv | https://info.arxiv.org/help/api/user-manual.html | No | Yes | Unknown | 2114 |
| Botlero | https://botlero.com/api/robots | No | Yes | Yes | 2115 |

Source commit: `2676ca49d557ef14a0f478311506dae947639028`

### Validation rules enforced

1. `### Science & Math` heading present.
2. Exact table header: `API | Description | Auth | HTTPS | CORS |`
3. Exact separator: `|:---|:---|:---|:---|:---|`
4. Each data row has exactly five columns.
5. Name cell contains a Markdown link `[Name](URL)`.
6. URL is non-empty.
7. Auth is one of: `No`, `apiKey`, `OAuth`, `X-Mashape-Key`, `User-Agent`.
8. HTTPS is `Yes` or `No`.
9. CORS is `Yes`, `No`, or `Unknown`.
10. Rows are alphabetically ordered (case-insensitive) within the section.
11. All three selected entries are present.
12. Selected entries have the expected URL, Auth, HTTPS and CORS values.
13. Selected APIs are explicitly validated against their immediate preceding and
    following neighbors (case-insensitive), including confirming that `Chempirical`
    correctly follows `Botlero`.

### Usage

```bash
python3 tools/course_checks/r02-t038.py --self-test   # offline fixture run
python3 tools/course_checks/r02-t038.py               # live README validation
python3 tools/course_checks/r02-t038.py --readme PATH # validate specific file
```

Exit code `0` = all checks pass. Exit code `1` = at least one error.

In live reporting:
- Task-specific selected APIs are validated and displayed with individual row status.
- If selected-entry ordering or neighbor ordering fails, offending selected rows are marked `[ERROR]` (never `[OK]`) and the selected ordering check is flagged as `[ERROR]`.
- Unrelated section-wide errors are reported separately from selected-entry validation.

### Fixture coverage

Fixtures and manifest are in `work/R02-T038/fixtures/`.

| Fixture | Expected exit | Expected error codes |
|---------|:-------------:|----------------------|
| `valid-all.md` | 0 | — |
| `malformed-row.md` | 1 | `bad_link`, `missing_entry` |
| `missing-entry.md` | 1 | `missing_entry` |
| `wrong-order.md` | 1 | `wrong_order` × 2 |
| `bad-link.md` | 1 | `empty_url`, `wrong_url` |
| `non-english.md` | 0 | — (non-English text preserved) |
| `paren-url.md` | 1 | `wrong_url` (URL has balanced parens) |
| `query-encoded.md` | 1 | `wrong_url` (URL has query + percent-encoding) |
| `header-error.md` | 1 | `bad_header`, `bad_separator` |
| `separator-error.md` | 1 | `bad_separator` |
| `unexpected-error.md` | 1 | `invalid_cors`, `wrong_cors` |
| `long-description.md` | 1 | `description_too_long` |
| `bad-padding.md` | 1 | `bad_padding` |
| `invalid-selected-auth.md` | 1 | `invalid_auth`, `wrong_auth` |
| `invalid-selected-cors.md` | 1 | `invalid_cors`, `wrong_cors` |
| `neighbor-order-error.md` | 1 | `wrong_order` (selected Botlero after neighbor Chempirical) |

### Limitations

- Validates only the `Science & Math` section.
- URL reachability is not checked (live HTTP out of scope).
- Two upstream pre-existing ordering issues (`NASA InSight`/`NASA ADS` and
  `OpenAlex`/`Open Ephemeris`) cause the live README validation to exit 1.
  These are real errors in the upstream README, not checker false positives.
  The selected entries themselves are correctly ordered.
