# R02-T048 — Explain Access Requirements: Authentication & Authorization

## Purpose

Validates that the **Authentication & Authorization** section entries have correct
Auth/HTTPS/CORS field values and that all entries contain valid markdown link syntax.
Documents the actual access requirements (registration, API key, payment, free tier)
for the three assigned entries.

## Assigned Entries

| Line | API Name | URL | Auth | HTTPS | CORS |
|------|----------|-----|------|-------|------|
| 306 | Auth0 | https://auth0.com | `apiKey` | Yes | Yes |
| 307 | GetOTP | https://otp.dev/en/docs/ | `apiKey` | Yes | No |
| 308 | MojoAuth | https://mojoauth.com | `apiKey` | Yes | Yes |

## Usage

```bash
# Offline self-test (uses fixtures, no network)
python3 tools/course_checks/r02-t048.py --self-test

# Live check against README.md
python3 tools/course_checks/r02-t048.py
```

## Fixtures (`work/R02-T048/fixtures/`)

| File | Description |
|------|-------------|
| `valid.md` | Three well-formed entries, all fields correct — must pass with 0 errors |
| `bad-auth.md` | One entry with invalid Auth value (`Bearer`) — must report Auth error |
| `bad-https.md` | One entry with invalid HTTPS value (`Maybe`) — must report HTTPS error |
| `no-link.md` | One entry with bare URL instead of `[Name](url)` — must report missing-link error |

## Checks Performed

1. **Auth field** — must be one of: `` `apiKey` ``, `` `OAuth` ``, `` `X-Mashape-Key` ``, `` `User-Agent` ``, `No`
2. **HTTPS field** — must be `Yes` or `No`
3. **CORS field** — must be `Yes`, `No`, or `Unknown`
4. **Link syntax** — API-name cell must contain a markdown hyperlink `[text](url)`
5. **Field comparison** — compares live values against expected values for all 3 assigned entries

## Notes

- All three assigned entries had correct metadata; no README.md changes were made.
- Access requirements documented in `work/R02-T048/api-verification.md`.
- No credentials were stored; only public documentation consulted.
