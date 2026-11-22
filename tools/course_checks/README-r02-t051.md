# R02-T051 — Redirect Checker: Currency Exchange

**Task:** R02-T051 · Verify redirects: Currency Exchange  
**File:** `tools/course_checks/r02-t051.py`  
**Standard library only** — no third-party packages required.

## Selected Entries

The checker targets exactly these three entries from the `### Currency Exchange`
section of `README.md` (source lines are parsed at runtime, not hardcoded):

| Entry | README Line | Current URL |
|-------|-------------|-------------|
| **Currencylayer** | L609 | https://currencylayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| **Exchangerate.host** | L610 | https://exchangerate.host?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| **Exchangeratesapi.io** | L611 | https://exchangeratesapi.io?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |

All three URLs carry `utm_*` tracking parameters, which are flagged for manual review
but are **never stripped automatically**.

## Usage

```bash
# Parse README and display the three entries (default mode)
python3 tools/course_checks/r02-t051.py

# Run offline fixture-based self-tests (exits non-zero on failure)
python3 tools/course_checks/r02-t051.py --self-test

# Fetch entries over the network and write evidence to work/R02-T051/report.json
python3 tools/course_checks/r02-t051.py --live

# Use a different README path
python3 tools/course_checks/r02-t051.py --readme /path/to/README.md --self-test
```

## Classification Labels

| Label | Meaning | Recommendation |
|-------|---------|----------------|
| `ok` | URL returns 200 with no redirects | `keep` |
| `moved_permanent` | 301 or 308 chain ending in 200 | `update_url` (if final URL differs) |
| `moved_temporary` | 302, 303, or 307 chain ending in 200 | `manual_review` |
| `redirect_loop` | The same URL appears twice in the chain | `manual_review` |
| `too_many_hops` | Chain exceeded the 5-hop budget | `manual_review` |
| `transient_failure` | Timeout, connection error, 5xx, or 429 | `manual_review` |
| `login_wall` | 401/403, redirect to `/login`, or 200 with a login form | `manual_review` |
| `client_error` | 4xx (other than 401/403/429) | `manual_review` |
| `needs_manual_review` | Ambiguous response (e.g., redirect with no Location header) | `manual_review` |

## Recommendation Rules

- **`keep`** — only when classification is `ok`.
- **`update_url`** — only when a *permanent* redirect (301/308) leads to a 200,
  the final URL differs from the original, and manual verification confirms the
  destination is the official API page.
- **`manual_review`** — everything else.
- **Never recommend removal** based on a single automated request failure.
  `transient_failure` always requires a human to re-check manually.

## Request Budget

| Parameter | Value |
|-----------|-------|
| Max hops per entry | 5 |
| Per-request timeout | 10 seconds |
| Max total requests (live mode) | 20 |
| Concurrency | Sequential (1 at a time) |

## Fixtures

Located in `tools/course_checks/fixtures/r02-t051/`. Each JSON file drives one
offline test case in `--self-test` mode:

| Fixture file | Scenario | Expected classification |
|---|---|---|
| `fixture_200.json` | Direct 200 OK | `ok` |
| `fixture_301_to_200.json` | 301 → 200 | `moved_permanent` |
| `fixture_302_to_200.json` | 302 → 200 | `moved_temporary` |
| `fixture_308_to_200.json` | 308 → 200 | `moved_permanent` |
| `fixture_redirect_loop.json` | A↔B loop | `redirect_loop` |
| `fixture_too_many_hops.json` | 6-step chain, budget=5 | `too_many_hops` |
| `fixture_timeout.json` | Socket timeout | `transient_failure` |
| `fixture_5xx.json` | 500 Server Error | `transient_failure` |
| `fixture_429.json` | 429 Too Many Requests | `transient_failure` |
| `fixture_connection_error.json` | DNS / connection refused | `transient_failure` |
| `fixture_login_wall_form.json` | 200 + password input | `login_wall` |
| `fixture_login_wall_401.json` | 401 Unauthorized | `login_wall` |
| `fixture_login_wall_403.json` | 403 Forbidden | `login_wall` |
| `fixture_login_wall_redirect.json` | Redirect to `/login` URL | `login_wall` |
| `fixture_client_error_404.json` | 404 Not Found | `client_error` |

## Negative-Test Proof

`--self-test` includes test case #17, which runs a deliberately wrong assertion
in a subprocess (`--_negative_assertion` flag) and verifies the exit code is
non-zero (1). This proves the assertion machinery exits non-zero on failure:

```
[17] Negative-test proof (subprocess — MUST exit non-zero)
  PASS  negative test exited with code 1 (non-zero ✓)
```

## Evidence

All evidence files are in `work/R02-T051/` (org-fork branch only):

| File | Contents |
|------|----------|
| `inputs.json` | Extracted README section and parsed entries with line numbers |
| `expected_vs_actual.json` | Expected vs actual for all 17 self-test cases |
| `results_table.md` | Human-readable results table |
| `tool_versions.json` | python3, git, OS versions |
| `report.json` | Live check output (populated by `--live`) |
| `manual_verification.md` | Table + exact commands for the live/manual step |

> **Note:** `work/R02-T051/` must be excluded from any later upstream PR to
> `public-apis/public-apis`. It is for the organisation-fork submission only.
