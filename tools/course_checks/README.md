# Course checks

## R02-T037

### Purpose

`tools/course_checks/r02-t037.py` checks the availability of the three APIs
assigned to R02-T037 and verifies that the catalogue metadata in the pinned
README can be parsed with its original line numbers. It uses only the Python
standard library, reads `README.md` locally, and restricts live requests to the
three selected entries.

### Selected entries

Category: **Games & Comics** (README heading at line 1260).

| API | README line | URL | Auth | HTTPS | CORS |
| --- | --- | --- | --- | --- | --- |
| AmiiboAPI | 1263 | https://amiiboapi.com/ | No | Yes | Yes |
| Animal Crossing: New Horizons | 1264 | http://acnhapi.com/ | No | Yes | Unknown |
| Astroworld | 1265 | https://api.astroworldmc.com | No | Yes | Yes |

These rows were identified by parsing the `### Games & Comics` table, not by
guessing from the API names.

### Failure classifications

The checker keeps these outcomes separate:

| Scenario | Classification |
| --- | --- |
| HTTP 200 | `Success` |
| HTTP 404 | `Missing resource (Not Found)` |
| HTTP 429 | `Rate Limited` |
| HTTP 403 | `Forbidden` |
| Request timeout | `Timeout` |
| DNS resolution failure | `DNS Failure` |
| HEAD 405/501 then GET 200 | `Success via GET fallback` |
| Other HTTP status | `HTTP Error` |
| Other network exception | `Network Error` |

Timeouts and DNS failures are classified from the underlying exception and
cannot be confused with each other. Forbidden and rate-limited responses are
never reported as missing resources. A 404 is reported as a missing resource
but never as a recommendation to remove the entry.

### HEAD-to-GET fallback

Each live check starts with HEAD. GET is used only when HEAD returns **405** or
**501**. If GET returns 200, the final result is `Success via GET fallback`
with method `GET`. If GET returns another status or raises an exception, that
GET result is preserved and reported. Other HEAD results, including 403, 404,
429, timeouts, and DNS failures, are not retried.

### Running the live checker

```bash
python3 tools/course_checks/r02-t037.py
python3 tools/course_checks/r02-t037.py --timeout 15
python3 tools/course_checks/r02-t037.py --readme README.md
```

Live checks run sequentially with a conservative default timeout of 10
seconds per request. The output includes the README line, URL, catalogue
metadata, request method, HTTP status or exception, and the final
classification. A completed live run exits 0 even when an endpoint is
unavailable; unavailable endpoints are observations, not checker failures.
Parsing/configuration errors exit 2.

### Running the offline self-tests

```bash
python3 tools/course_checks/r02-t037.py --self-test
```

The self-test makes **no network requests**. It injects a fake transport built
from the JSON fixtures and also checks that the three selected README rows and
their exact line numbers are parsed. Any mismatch, including a violated
negative assertion, produces a non-zero exit status.

A different fixture directory can be supplied for testing the test harness:

```bash
python3 tools/course_checks/r02-t037.py --self-test --fixtures work/R02-T037/fixtures
```

### Fixtures

Fixtures live in `work/R02-T037/fixtures/`. Each JSON file defines simulated
HEAD/GET responses or exceptions, an explicit expected classification, method
and status, and negative assertions that must not occur.

| Fixture | Simulated result | Expected classification |
| --- | --- | --- |
| `01_http_200.json` | HEAD 200 | `Success` |
| `02_http_404.json` | HEAD 404 | `Missing resource (Not Found)` |
| `03_http_429.json` | HEAD 429 | `Rate Limited` |
| `04_http_403.json` | HEAD 403 | `Forbidden` |
| `05_head_405_get_200.json` | HEAD 405, GET 200 | `Success via GET fallback` |
| `06_timeout.json` | HEAD raises timeout | `Timeout` |
| `07_dns_failure.json` | HEAD raises DNS error | `DNS Failure` |
| `08_head_501_get_200.json` | HEAD 501, GET 200 | `Success via GET fallback` |
| `09_head_405_get_429.json` | HEAD 405, GET 429 | `Rate Limited` (GET preserved) |

### Actual test results

Recorded on 2026-11-17 (see `work/R02-T037/actual-results.txt` for full logs):

- Offline self-test: **9/9 fixtures passed**, README parser check passed, exit 0.
  The same suite also passed with proxy variables pointed at a closed port,
  confirming it makes no network requests.
- Negative assertion demonstrations with deliberately invalid fixtures: exit 1.
- Live checker (final run): AmiiboAPI `Success` (HEAD 200), Animal Crossing:
  New Horizons `Network Error` (connection closed), Astroworld `Success`
  (HTTP 200); exit 0. An earlier run observed AmiiboAPI `Timeout` on HEAD,
  which illustrates why live observations are treated as point-in-time only.
- `git diff --check`: no whitespace errors.

Live results vary by network path and time. They are not used to change the
catalogue automatically.

### Metadata verification summary

No README metadata corrections were needed:

- **AmiiboAPI**: official documentation says no authentication and GET-only.
  HTTPS is available, and a live API mirror returned
  `Access-Control-Allow-Origin: *`; existing `No / Yes / Yes` remains supported.
- **Animal Crossing: New Horizons**: the official archived repository says no
  authentication and supports HTTP or HTTPS. CORS is not documented, so
  `Unknown` remains. The service did not respond during the live check, so no
  live CORS conclusion was drawn.
- **Astroworld**: official documentation states no auth, HTTPS, and CORS
  enabled; live `/api/health` returned HTTP 200 with
  `Access-Control-Allow-Origin: *`. Existing `No / Yes / Yes` is confirmed.

See `work/R02-T037/evidence.md` and `work/R02-T037/api-verification.txt` for
sources and the distinction between documentation and live observations.

### Limitations

- Live checks observe one network path at one point in time; they do not prove
  permanent availability or unavailability.
- HEAD may be blocked or slow even when GET works. Only 405/501 trigger the GET
  fallback, so a HEAD timeout remains `Timeout`.
- A 403, 404, 429, timeout, or DNS failure does not prove incorrect metadata.
- The checker does not send an `Origin` header or perform CORS preflight
  requests; CORS verification relies on official documentation and observed
  response headers.
- No retries are attempted, and no removal recommendation is made from a single
  failed request.
