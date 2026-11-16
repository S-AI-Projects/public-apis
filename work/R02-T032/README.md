# R02-T032 — Redirect chain verification

- **Student:** Apurav Agarwal
- **URN:** `e26b07f0885`
- **Assignment:** 2 of 10
- **Task:** R02-T032
- **Required branch:** `student/e26b07f0885/R02-T032`
- **Base:** `upstream/master` at `2676ca49d557ef14a0f478311506dae947639028`
- **Observation date (UTC):** 2026-11-16
- **Environment:** Python 3.15.2, CPython, Darwin 27.2.0 (arm64)

Task 1 (`R02-T031`) is a separate branch and is not merged, copied or
cherry-picked into this work. The checker and documentation here are new
R02-T032 files based on the upstream master tree.

## 1. Scope and assigned entries

Only these three rows in the `Food & Drink` section of the root `README.md`
were inspected or requested:

| # | API | README URL | README line | Auth | HTTPS | CORS |
|---|---|---|---|---|---|---|
| 1 | BaconMockup | `https://baconmockup.com/` | 1220 | No | Yes | Yes |
| 2 | CalorieNinjas | `https://calorieninjas.com/api` | 1221 | `apiKey` | Yes | Yes |
| 3 | Chomp | `https://chompthis.com/api/` | 1222 | `apiKey` | Yes | Unknown |

The README line numbers and exact row text are also recorded in
`work/R02-T032/inputs.json`. They were resolved from the pinned README and
verified by the self-test. No unrelated API entries were checked or modified.

## 2. Implementation

New checker:

```text
tools/course_checks/r02-t032.py
```

New documentation:

```text
tools/course_checks/README.md
```

The checker uses only the Python standard library. It performs explicit
single-request `GET` calls with `http.client`, so it controls redirect
following itself rather than relying on a helper that silently hides hops.

Key behaviour:

- Statuses followed: `301`, `302`, `303`, `307`, `308`.
- `Location` is resolved with `urljoin`; relative, absolute-path and
  protocol-relative destinations are supported.
- Maximum redirects is configurable. The live default is 5 redirects, which
  permits at most 6 requests per URL.
- A repeated normalized URL is `REDIRECT_LOOP`; reaching the budget without a
  repeat is `REDIRECT_LIMIT`.
- Connection and read timeouts are separate. DNS resolution has a bounded
  caller wait, but the underlying resolver thread is not cancellable; a late
  result is ignored. This limitation is explicit in the code and documentation.
- Each destination is resolved once per hop and every returned address is
  validated. The socket then connects directly to a validated numeric address;
  the connection path does not resolve the host name again.
- TCP connection attempts across the validated addresses share one connection
  deadline. TLS handshakes and reads use the configured timeouts.
- The original host name is retained for the HTTP `Host` header, TLS SNI and
  certificate host name verification. Certificate verification remains enabled.
- The actual connected peer address is compared with the validated address; a
  mismatch is `BLOCKED_TARGET`.
- Missing or malformed `Location`, unsupported schemes, invalid URLs,
  connection failures, DNS failures, TLS failures and timeouts are handled
  explicitly.
- Each request, including every redirect hop, is preceded by an SSRF check
  (loopback, private, link-local, multicast, reserved, unspecified). The live
  path never allows non-global destinations. The self-test allowance permits
  only loopback fixture addresses.
- No API keys, credentials, authenticated calls, form submissions or writes are
  used. The `User-Agent` identifies the checker as an educational tool.
- Every `2xx` HTML body, direct or redirected, is read only up to 32 KiB for
  explicit login-form detection. A direct login page is `AUTH_WALL`; an
  ordinary direct page is `OK`; an ordinary redirected page is `MOVED`.
- A timeout during that required read is `TIMEOUT`, and a body-read failure
  (including an incomplete body) is `CONNECTION_ERROR`; neither is reported as
  `OK`/`MOVED`. `204`/`205` and non-HTML bodies are not read.
- Targets are fixed in the script; there is no arbitrary-URL CLI option.

Classification model:

| Classification | Meaning |
|---|---|
| `OK` | Original URL returned a valid `2xx`; no redirects. |
| `MOVED` | Redirect chain ended at a valid `2xx` destination. |
| `REDIRECT_LOOP` | A destination repeated an already-visited URL. |
| `REDIRECT_LIMIT` | Redirect/request budget exhausted. |
| `TIMEOUT` | DNS caller wait, connect, TLS, send, read or required body-read timeout. |
| `DNS_FAILURE` | Host name could not be resolved. |
| `CONNECTION_ERROR` | Connection failed, closed before a response, or failed while reading a required HTML body. |
| `TLS_ERROR` | TLS negotiation or certificate verification failed. |
| `TRANSIENT_FAILURE` | Temporary HTTP/network condition (`408`, `425`, `429`, `5xx`). |
| `AUTH_WALL` | HTTP `401`/`403`, login/IdP redirect, or explicit login form. |
| `HTTP_ERROR` | Definitive HTTP error or unexpected redirect status. |
| `INVALID_URL` | Invalid/unsafe URL, including malformed redirect target. |
| `UNSUPPORTED_SCHEME` | Destination is not `http://` or `https://`. |
| `BLOCKED_TARGET` | Non-global destination refused before a request. |

The full classification definitions, safety policy and usage are documented in
`tools/course_checks/README.md`.

## 3. Offline tests

The self-test starts a local deterministic mock HTTP server on `127.0.0.1` and
does not use the internet. It contains **57 resolver cases** and **11
consistency checks**. The resolver cases cover direct `200`, `201`, `204` and
`206` successes; `301`/`302`/`303`/`307`/`308`; relative, multi-hop and
query-preserving redirects; loop and budget exhaustion; missing/malformed
`Location`; unsupported schemes; `401`/`403`; `408`/`425`/`429`/`500`/`503`;
unexpected `300`/`304`; redirected `403`/`500`; login redirects; a direct
password form; a direct ordinary HTML page; a direct HTML page without login
indicators; direct and redirected HTML body-read timeouts; a direct truncated
body (body-read error); a redirect to a private address that is revalidated and
blocked; DNS failure; a read timeout; a closed connection; invalid URLs; and the
SSRF guard.

The consistency checks also prove that a host resolved to a loopback address is
connected using that validated address without a second DNS lookup, with the
original `Host` header and a matching peer address. They additionally cover the
bounded DNS wait, peer-address mismatch handling, enabled TLS verification, the
loopback-only self-test policy and URL normalization.

Commands and reported results:

```text
python3 tools/course_checks/r02-t032.py --self-test
  -> 57/57 resolver cases passed; 11/11 consistency checks passed; exit 0

python3 -O tools/course_checks/r02-t032.py --self-test
  -> 57/57 resolver cases passed; 11/11 consistency checks passed; exit 0

python3 -OO tools/course_checks/r02-t032.py --self-test
  -> 57/57 resolver cases passed; 11/11 consistency checks passed; exit 0

python3 -m py_compile tools/course_checks/r02-t032.py
  -> exit 0
```

The checker contains no Python `assert` statements; all test validation uses
explicit checks so optimization flags cannot disable it. The exact command
outputs are captured in `work/R02-T032/validation.txt`. Expected outcomes are
in `expected-results.json`; actual outcomes are in `actual-results.json`.

## 4. Live verification

Date: **2026-11-16** (UTC). Method: one sequential `GET` per assigned URL, no
credentials, no retries, 5 s connect/read timeouts, maximum 5 redirects, 32 KiB
body cap. All three requests were made from the same machine and network.

| API | Observed | HTTP | Redirect chain | Final observed URL | Requests |
|---|---|---|---|---|---|
| BaconMockup | `OK` | 200 | none | `https://baconmockup.com/` | 1 |
| CalorieNinjas | `OK` | 200 | none | `https://calorieninjas.com/api` | 1 |
| Chomp | `OK` | 200 | none | `https://chompthis.com/api/` | 1 |

Validated/connected peer addresses: BaconMockup `162.243.9.212`, CalorieNinjas
`13.225.5.128`, Chomp `162.243.43.15`; each peer address equaled its validated
address.

Live observation window recorded in `live-results.json`:
`2026-11-16T12:49:07Z` to `2026-11-16T12:49:10Z`.

Each result records a connected peer address equal to its validated address,
confirming that the connection did not re-resolve to a different address. All
three `2xx` HTML bodies were inspected up to the 32 KiB cap; none contained an
explicit login form. CalorieNinjas and Chomp exceeded the cap, so their results
record `body_truncated=true`; the inspected prefix had no login indicators, so
both remain `OK`. No body-read timeout or body-read error occurred.

No redirect was observed for any of the three assigned URLs. The live result
does not claim that the documented API endpoints are functional, because no
API endpoint was called and no API key was used. It also does not establish
CORS support. These limitations are listed in `live-results.json` and in the
checker documentation.

## 5. Official documentation verification

Detailed evidence is in `api-verification.md`. Summary:

- **BaconMockup** — official homepage is `https://baconmockup.com/`; it
  documents the width/height image URL pattern and requires no API key.
  HTTPS is used. CORS is not documented on the official page, so the existing
  `Yes` is preserved but not independently confirmed.
- **CalorieNinjas** — official API documentation is
  `https://calorieninjas.com/api`; it documents a free account, an API key and
  the `X-Api-Key` header. HTTPS is used. CORS is not documented, so the
  existing `Yes` is preserved but not independently confirmed. The page also
  displays a migration notice pointing to API Ninjas; see below.
- **Chomp** — official API landing page is `https://chompthis.com/api/`, with
  documentation at `https://chompthis.com/api/v2/docs/`. It documents API-key
  authentication and HTTPS. CORS is not documented; the existing `Unknown`
  value is preserved.

The checker distinguishes documented facts, direct HTTP observations,
inferences and unknown/unverified information in `api-verification.md`.

## 6. README decision

**No row in the root `README.md` was modified.** No entry was removed or added.
The exact source rows are at lines 1220–1222.

Reasons:

- **BaconMockup:** the listed URL is the official service homepage, returns
  HTTP 200 directly, and the description/auth/HTTPS fields are consistent with
  the official page. There is no evidence requiring a correction.
- **CalorieNinjas:** the listed URL is the official CalorieNinjas API
  documentation page and returns HTTP 200 directly. The page displays an
  official notice that CalorieNinjas is migrating to API Ninjas. This is a
  vendor migration notice, not a redirect, and the CalorieNinjas documentation
  and URL remain live. Replacing the row with API Ninjas would change the
  service identity and scope rather than correct a broken redirect. The notice
  is recorded as a follow-up item for maintainers; no edit was made under this
  redirect-verification task.
- **Chomp:** the listed URL is the official API landing/pricing page, returns
  HTTP 200 directly, and the description/auth/HTTPS fields are consistent with
  the official page and its `/api/v2/docs/` documentation. There is no
  evidence requiring a correction.

A single automated failure would not have been sufficient to remove any entry.
In this run none of the three live requests failed.

## 7. Evidence files

| File | Contents |
|---|---|
| `README.md` | This summary, methodology and decisions. |
| `inputs.json` | Fixed target list, README rows/lines, parameters, safety notes. |
| `expected-results.json` | Expected offline fixture outcomes and consistency checks. |
| `actual-results.json` | Actual offline results from the latest self-test. |
| `live-results.json` | Dated live observations, statuses, chains, final URLs, validated/peer addresses, body-inspection flags and limitations. |
| `environment.txt` | Python/OS/git versions and README SHA-256. |
| `api-verification.md` | Official documentation evidence, facts and unknowns. |
| `validation.txt` | Commands and summaries from the validation run. |

No API keys, secrets, personal access tokens, large response bodies or
machine-specific hostnames are included.

## 8. Reproduction commands

```bash
# Offline, deterministic
python3 tools/course_checks/r02-t032.py --self-test
python3 -O tools/course_checks/r02-t032.py --self-test
python3 -OO tools/course_checks/r02-t032.py --self-test
python3 -m py_compile tools/course_checks/r02-t032.py

# Live, fixed targets only
python3 tools/course_checks/r02-t032.py --live

# Repository hygiene
git diff --check
git status --short
git diff --stat
git diff
git log --oneline upstream/master..HEAD
```

## 9. Limitations

- Live results are a single point-in-time observation and can vary by network,
  geography, CDN, rate limiting and bot protection.
- DNS resolution has a bounded caller wait, but an already-running resolver
  operation cannot be cancelled. The late result is ignored, and the connection
  uses only addresses from the validated lookup.
- Every `2xx` HTML body, direct or redirected, is inspected only up to 32 KiB.
  A login form beyond that prefix, or a response without a `text/html` content
  type, may not be detected. `204`/`205` and non-HTML bodies are not read.
- The checker verifies landing/documentation pages, not authenticated API
  endpoints or response schemas.
- CORS was not inferred from a browser-openable page; official CORS evidence
  was not available for any of the three services.
- The CalorieNinjas migration notice is recorded but was not acted on because
  it is a vendor migration rather than a redirect or a demonstrably broken
  assigned URL.
- No claim is made that a single failed request would justify deleting an
  entry.
