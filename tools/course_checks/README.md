# R02-T049 — Repeatable Maintenance Pass: Entertainment

## Purpose

Produces a one-command scoped maintenance report for the **Entertainment** section of `README.md`.
Separates observed facts (field values, line numbers) from recommendations (Unknown CORS, HTTP-only entries)
and generates stable, reproducible output from both fixtures and live README.

## Assigned Entries

| Line | API Name | URL | Auth | HTTPS | CORS |
|------|----------|-----|------|-------|------|
| 1032 | Anycrap | https://anycrap.shop/developers | `apiKey` | Yes | Yes |
| 1033 | Bucketlist Dream of the Day | https://bucketlist.nl/samenwerken?lang=en#droom-van-de-dag | No | Yes | Yes |
| 1034 | chucknorris.io | https://api.chucknorris.io | No | Yes | Unknown |

## Usage

```bash
# Offline self-test (uses fixtures, no network)
python3 tools/course_checks/r02-t049.py --self-test

# Live maintenance report against README.md
python3 tools/course_checks/r02-t049.py
```

## Fixtures (`work/R02-T049/fixtures/`)

| File | Description |
|------|-------------|
| `valid.md` | 3 well-formed entries, all fields correct — 0 errors, 3 facts generated |
| `unknown-cors.md` | Entry with CORS=Unknown — generates recommendation to verify CORS |
| `bad-fields.md` | Entry with invalid Auth (`Bearer`) and HTTPS (`Maybe`) — generates field errors |
| `no-link.md` | Entry with bare URL (no markdown link) — generates missing-link error |

## Maintenance Checks Performed

1. **Fact extraction** — records exact line number, Auth, HTTPS, CORS values as found
2. **Field validation** — Auth, HTTPS, CORS values checked against allowed value sets
3. **Link syntax** — API-name cell must contain a valid markdown hyperlink `[text](url)`
4. **Recommendations** — flags `Unknown` CORS and `No` HTTPS entries for follow-up
5. **Assigned-entry comparison** — compares live values against expected metadata for 3 assigned entries
6. **Report stability** — same input always produces same output (no randomness, no live calls)

## Notes

- chucknorris.io's `Unknown` CORS is correct; no confirmed documentation exists for its CORS policy.
- All 3 assigned entries verified as accurate; no README.md changes were made.
- Report explicitly separates Observed Facts from Recommendations.
