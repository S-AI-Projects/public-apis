# Coursework Checks — R02-T026: Verify Entry Metadata (Development)

This directory contains deterministic offline verification checkers and offline test fixtures for coursework task R02-T026.

## 1. Selected Entries & Source Line Numbers

Category: **Development** (starts at line 663 in root `README.md`)

| API Name | Source Line | URL |
|:---|:---|:---|
| **Userstack** | Line 666 | `https://userstack.com/?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers` |
| **24 Pull Requests** | Line 667 | `https://24pullrequests.com/api` |
| **Aether Bridge** | Line 668 | `https://a-to-mind.com` |

---

## 2. Official Verification Sources

1. **Userstack**:
   - Official API Documentation: `https://docs.apilayer.com/userstack/docs/api-documentation` / `https://userstack.com/documentation`
   - Authentication scheme: Userstack requires an API Access Key supplied as `access_key=YOUR_ACCESS_KEY` in the request query string or `apikey` in headers. It does not use OAuth.
   - HTTPS: Supported (`https://api.userstack.com/detect`).
   - CORS: `Unknown` — no sufficiently authoritative documentation was found to classify it as Yes/No for this task.

2. **24 Pull Requests**:
   - Official API Documentation: `https://24pullrequests.com/api`
   - Authentication scheme: Unauthenticated public REST endpoints (`No`).
   - HTTPS: Supported (`Yes`).
   - CORS: `No`.
     - *Documentation & Source Code Findings:* Official API documentation advertises "JSON-P Callbacks" (`?callback=foo`) for cross-domain browser embedding. JSONP is a legacy script-tag injection workaround and does not constitute native HTTP-header-based CORS. Examination of the open-source Ruby on Rails repository (`24pullrequests/24pullrequests`) confirms no CORS middleware (e.g. `rack-cors`) or CORS response header configuration exists.
     - *Observed Live Behavior:* Live HTTP requests to `/users.json`, `/projects.json`, and `/pull_requests.json` with cross-origin `Origin` headers confirm the absence of any `Access-Control-Allow-Origin` header (with `x-permitted-cross-domain-policies: none` returned instead). Preflight `OPTIONS` requests fail with `404 Not Found`. Cross-origin browser `fetch()` or `XMLHttpRequest` requests are blocked by modern browser Same-Origin Policy.

3. **Aether Bridge**:
   - Official Documentation & Domain: `https://a-to-mind.com` / `https://a-to-mind.com/llms.txt` / `https://a-to-mind.com/openapi.json`
   - Authentication scheme: API key (`apiKey`).
   - HTTPS: Supported (`Yes`).
   - CORS: `Unknown` — no sufficiently authoritative documentation was found to classify it as Yes/No for this task.

---

## 3. Observed vs Proposed Metadata

| API | Field | Original in README | Verified Value | Action | Reason |
|:---|:---|:---|:---|:---|:---|
| **Userstack** | Auth | `` `OAuth` `` | `` `apiKey` `` | **Corrected** | Official documentation verifies authentication is via API Access Key (`access_key`), not OAuth. |
| **Userstack** | HTTPS | `Yes` | `Yes` | Preserved | Verified HTTPS endpoint. |
| **Userstack** | CORS | `Unknown` | `Unknown` | Preserved | Consistent with repository conventions for APILayer APIs. |
| **24 Pull Requests** | Auth | `No` | `No` | Preserved | Open public endpoints without auth. |
| **24 Pull Requests** | HTTPS | `Yes` | `Yes` | Preserved | Verified HTTPS endpoint. |
| **24 Pull Requests** | CORS | `Yes` | `No` | **Corrected** | JSONP callbacks do not constitute native CORS. Live probing confirmed absence of `Access-Control-Allow-Origin` on GET endpoints and OPTIONS returned 404, blocking browser cross-origin requests. |
| **Aether Bridge** | Auth | `` `apiKey` `` | `` `apiKey` `` | Preserved | Uses API key authentication. |
| **Aether Bridge** | HTTPS | `Yes` | `Yes` | Preserved | Verified HTTPS endpoint. |
| **Aether Bridge** | CORS | `Unknown` | `Unknown` | Preserved | Verified catalogue value. |

---

## 4. Offline Fixture Test Coverage

Fixtures are located under `tools/course_checks/fixtures/r02-t026/`:

1. `valid_entries.md`: Positive test fixture containing all three selected entries with compliant 5-column table structure and verified metadata.
2. `missing_required_field.md`: Negative test fixture with a selected entry row having fewer than 5 columns (4 columns).
3. `extra_column.md`: Negative test fixture with a selected entry row having more than 5 columns (6 columns).
4. `malformed_row.md`: Negative test fixture where a selected entry row lacks markdown link formatting or pipe delimiters.
5. `invalid_auth.md`: Negative test fixture containing unapproved Auth values (`token`, `BasicAuth`) not listed in `CONTRIBUTING.md`.
6. `invalid_https_cors.md`: Negative test fixture containing non-standard HTTPS and CORS values (`True`, `All`, `Maybe`).
7. `incorrect_metadata.md`: Negative test fixture containing syntactically valid but factually mismatched metadata against authoritative ground truth.
8. `line_tracking.md`: Tests precise source line number reporting across varying file offsets.
9. `url_query_params.md`: Validates that complex query parameters (`?utm_source=...&format=json&access_key=...`) are preserved verbatim.
10. `url_fragments_special_chars.md`: Validates that URL fragments (`#json-p-callbacks`) and percent-encoded/special characters are preserved verbatim.
11. `outside_development.md`: Validates that rows with matching names appearing outside the `### Development` section are strictly ignored.
12. `url_parentheses.md`: Validates that Markdown URLs containing balanced parentheses (e.g. `api(v1)/detect?query=(ua)`) are extracted correctly without truncation.
13. `escaped_pipe_url.md`: Validates that escaped pipes (`\|`) inside Markdown URLs are preserved intact and do not cause column-splitting errors.
14. `literal_pipe_url.md`: Validates that unescaped literal pipes (`|`) inside Markdown URLs are explicitly rejected with an informative error.
15. `duplicate_entries.md`: Validates that duplicate occurrences of a selected API are detected and rejected, even if the total row count equals 3.
16. `missing_entry.md`: Validates that missing selected APIs are explicitly detected and reported.

---

## 5. Usage & Verification Commands

### Run Deterministic Self-Tests
```bash
python3 tools/course_checks/r02-t026.py --self-test
```

### Validate Root README.md
```bash
python3 tools/course_checks/r02-t026.py
```

### Python Bytecode Compilation Check
```bash
python3 -m py_compile tools/course_checks/r02-t026.py
```

### Git Whitespace Check
```bash
git diff --check
```
