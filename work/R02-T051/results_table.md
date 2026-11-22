# R02-T051 Self-Test Results

Recorded: 2026-11-22T08:39:09+00:00
Tool: `python3 tools/course_checks/r02-t051.py --self-test`
Exit code: **0** (all pass)
Negative-test exit code: **1** (non-zero ✓)

## Fixture Test Results

| # | Test Case | Fixture | Expected Classification | Actual | Hop Count | Recommendation | Result |
|---|-----------|---------|------------------------|--------|-----------|----------------|--------|
| 1 | Direct 200 OK | fixture_200.json | ok | ok | 0 | keep | ✅ PASS |
| 2 | 301 → 200 | fixture_301_to_200.json | moved_permanent | moved_permanent | 1 | update_url | ✅ PASS |
| 3 | 302 → 200 | fixture_302_to_200.json | moved_temporary | moved_temporary | 1 | manual_review | ✅ PASS |
| 4 | 308 → 200 | fixture_308_to_200.json | moved_permanent | moved_permanent | 1 | update_url | ✅ PASS |
| 5 | Redirect loop | fixture_redirect_loop.json | redirect_loop | redirect_loop | 2 | manual_review | ✅ PASS |
| 6 | Too many hops (>5) | fixture_too_many_hops.json | too_many_hops | too_many_hops | 5 | manual_review | ✅ PASS |
| 7 | Timeout | fixture_timeout.json | transient_failure | transient_failure | 0 | manual_review | ✅ PASS |
| 8 | 5xx server error | fixture_5xx.json | transient_failure | transient_failure | 0 | manual_review | ✅ PASS |
| 9 | 429 rate limited | fixture_429.json | transient_failure | transient_failure | 0 | manual_review | ✅ PASS |
| 10 | Connection error | fixture_connection_error.json | transient_failure | transient_failure | 0 | manual_review | ✅ PASS |
| 11 | Login wall (200 + form) | fixture_login_wall_form.json | login_wall | login_wall | 0 | manual_review | ✅ PASS |
| 12 | Login wall (401) | fixture_login_wall_401.json | login_wall | login_wall | 0 | manual_review | ✅ PASS |
| 13 | Login wall (403) | fixture_login_wall_403.json | login_wall | login_wall | 0 | manual_review | ✅ PASS |
| 14 | Login wall (redirect to /login) | fixture_login_wall_redirect.json | login_wall | login_wall | 1 | manual_review | ✅ PASS |
| 15 | Client error (404) | fixture_client_error_404.json | client_error | client_error | 0 | manual_review | ✅ PASS |
| 16 | README parser | README.md | 3 entries, with line numbers | 3 entries (L609, L610, L611) | — | — | ✅ PASS |
| 17 | **Negative-test proof** | fixture_timeout.json | wrong expectation → exit 1 | exit code = 1 | — | — | ✅ PASS |

**Total: 17/17 passed**

## Parsed README Entries (Actual)

| Entry | README Line | URL | Auth | HTTPS | CORS | UTM Flagged |
|-------|-------------|-----|------|-------|------|-------------|
| Currencylayer | L609 | https://currencylayer.com?utm_source=... | `apiKey` | Yes | Unknown | ✓ |
| Exchangerate.host | L610 | https://exchangerate.host?utm_source=... | `apiKey` | Yes | Unknown | ✓ |
| Exchangeratesapi.io | L611 | https://exchangeratesapi.io?utm_source=... | `apiKey` | Yes | Yes | ✓ |

## README.md Status

**No changes made.** The sandbox network was unavailable during automated checks,
so all three live entries were classified as `transient_failure` (connection_error).
Per the task rules, **no entry may be removed or altered based solely on a single
automated request failure.** See `manual_verification.md` for the commands to run
and the evidence to record before any catalogue correction is considered.
