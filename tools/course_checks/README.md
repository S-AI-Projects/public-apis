# R02-T047 — Formatting Check: Sports & Fitness

## Purpose

Validates that all entries in the **Sports & Fitness** section of `README.md` follow the
project's pipe-delimited table formatting rules, contain valid markdown link syntax, and
are sorted alphabetically by API name.

## Assigned Entries

| Line | API Name | URL |
|------|----------|-----|
| 2355 | 5DollarFootball | https://5dollarfootballapi.com/ |
| 2356 | AcesAPI | https://acesapi.com/docs |
| 2357 | API-FOOTBALL | https://www.api-football.com/documentation-v3 |

## Usage

```bash
# Offline self-test (uses fixtures, no network)
python3 tools/course_checks/r02-t047.py --self-test

# Live check against README.md
python3 tools/course_checks/r02-t047.py
```

## Fixtures (`work/R02-T047/fixtures/`)

| File | Description |
|------|-------------|
| `valid.md` | Well-formed entry with non-ASCII characters — must pass |
| `malformed.md` | Row missing closing pipe — must report line-number error |
| `bad-link.md` | Entry with bare URL instead of `[Name](url)` syntax — must report error |
| `out-of-order.md` | Two entries with B before A — must report ordering error |

## Checks Performed

1. **Row structure** — every data row must start and end with `|`
2. **Link syntax** — the API-name cell must contain a markdown hyperlink `[text](url)`
3. **Column count** — rows must have exactly 6 pipe-separated fields (5 columns)
4. **Alphabetical ordering** — entries must be sorted case-insensitively by API name
   (pre-existing anomalies not involving assigned entries are reported but not flagged as failures)

## Notes

- Never removes entries for 4xx/5xx HTTP responses; only formatting is checked here.
- Cloudflare WAF 403 on API-FOOTBALL is documented in `work/R02-T047/api-verification.md`.
- No `README.md` changes were made by this checker.
