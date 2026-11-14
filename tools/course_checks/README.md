# Coursework Checks — R02-T027: Classify Failures Correctly (Machine Learning)

This directory contains deterministic offline verification checkers, failure classification rules, and test fixtures for coursework task R02-T027.

---

## 1. Selected Entries & Source Line Numbers

Category: **Machine Learning** (starts at line 1744 in root `README.md`)

| API Name | Source Line | URL |
|:---|:---|:---|
| **AI Economics Tools** | Line 1747 | `https://piszczek.pl/tools/api` |
| **AI For Thai** | Line 1748 | `https://aiforthai.in.th/index.php` |
| **AI Stupid Level** | Line 1749 | `https://aistupidlevel.info/api-docs` |

---

## 2. Official Verification Sources

1. **AI Economics Tools**:
   - Official API Documentation: `https://piszczek.pl/tools` / `https://piszczek.pl/openapi.json`
   - Description: Token cost, LLM energy, agent-hour and Proof-Adjusted Autonomy calculators by Michał Piszczek.
   - Authentication: `No` (unauthenticated public API).
   - HTTPS: `Yes`.
   - CORS: `Yes` (returns `Access-Control-Allow-Origin: *`).
   - Live HTTP status: `200 OK` on both HEAD and GET.

2. **AI For Thai**:
   - Official API Documentation: `https://aiforthai.in.th` / `https://api.aiforthai.in.th`
   - Description: Free Various Thai AI API.
   - Authentication: `apiKey` (NECTEC Thai AI platform requires an API key).
   - HTTPS: `Yes`.
   - CORS: `Yes`.
   - Live HTTP status: `200 OK` on both HEAD and GET.

3. **AI Stupid Level**:
   - Official API Documentation: `https://aistupidlevel.info/api-docs`
   - Description: Benchmark scores, rankings and drift data for major LLM APIs, re-measured on a fixed schedule.
   - Authentication: `apiKey`.
   - HTTPS: `Yes`.
   - CORS: `No` (documented in commit d752c5f0; cross-origin headers not emitted).
   - Live HTTP status: `200 OK` on both HEAD and GET.

---

## 3. Failure Classification Rules

When probing API endpoints, outcomes are mapped strictly to the following labels:

| Outcome / Status Code | Failure Classification | Notes |
|:---|:---|:---|
| `HTTP 200` | `success` | Endpoint is accessible and functional. |
| `HTTP 404` | `missing_resource` | Target resource was not found. |
| `HTTP 403` | `forbidden` | Request forbidden by access control. |
| `HTTP 429` | `rate_limited` | Exceeded request quota/rate limit. |
| Timeout | `timeout` | Connection or socket read timed out. |
| DNS resolution error | `dns_failure` | Hostname cannot be resolved via DNS. |
| Other HTTP errors | `http_{status_code}` | E.g., `http_500`, `http_502`, `http_503`, `http_401`. |

---

## 4. HEAD-to-GET Fallback Policy

- Probing initially attempts an HTTP `HEAD` request to avoid unnecessary bandwidth.
- If the endpoint responds with HTTP `405 Method Not Allowed` or `501 Not Implemented`, the checker automatically retries using an HTTP `GET` request.
- A `HEAD 405` (or `501`) followed by `GET 200` is classified as `success`.
- Any error on the `GET` fallback is classified according to the GET response.

---

## 5. Manual Confirmation Policy

- Automated request failures (including HTTP 404 `missing_resource`) do **not** automatically trigger removal of an API entry from the catalogue.
- A single 404 or temporary network failure must never be treated as proof that an API is dead.
- Removal is **only** recommended when a resource is manually confirmed missing by human review (`manually_confirmed_missing: True`).
- All unconfirmed 404s and failures are classified with `removal_recommended: False` and marked for manual review.

---

## 6. Offline Fixture Test Coverage

Fixtures are located under `tools/course_checks/fixtures/r02-t027/`:

1. `valid_entries.md`: Baseline table structure for all three entries under `### Machine Learning`.
2. `line_tracking.md`: Tests that source line numbers (lines 13, 14, 15) are tracked accurately across varying offsets.
3. `outside_category.md`: Tests that entries under other categories (e.g. `### Animals`) are ignored.
4. `http_200.json`: Validates HTTP 200 $\to$ `success`.
5. `http_404.json`: Validates HTTP 404 $\to$ `missing_resource`.
6. `http_429.json`: Validates HTTP 429 $\to$ `rate_limited`.
7. `http_403.json`: Validates HTTP 403 $\to$ `forbidden`.
8. `head_405_get_200.json`: Validates that HEAD 405 retried with GET 200 is classified as `success`.
9. `timeout.json`: Validates socket/connection timeout $\to$ `timeout`.
10. `dns_failure.json`: Validates DNS resolution failure $\to$ `dns_failure`.
11. `other_http_errors.json`: Validates distinct error labels for other HTTP status codes (`http_500`, `http_502`, `http_503`, `http_401`).
12. `manually_confirmed_missing.json`: Validates that a 404 with manual confirmation results in `removal_recommended: True`.
13. `unconfirmed_missing.json`: Validates that a 404 without manual confirmation results in `removal_recommended: False`.

---

## 7. Usage & Validation Commands

### Run Deterministic Offline Self-Tests
```bash
python3 tools/course_checks/r02-t027.py --self-test
```

### Run Live Failure Classification Check
```bash
python3 tools/course_checks/r02-t027.py
```

### Python Bytecode Compilation Check
```bash
python3 -m py_compile tools/course_checks/r02-t027.py
```

### Git Whitespace Check
```bash
git diff --check
```
