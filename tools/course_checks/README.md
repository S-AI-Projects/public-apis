# Coursework Checks — R02-T030: Document a Repeatable Maintenance Pass (Animals)

This directory contains deterministic offline verification checkers, repeatable maintenance report models, and test fixtures for coursework task R02-T030.

---

## 1. Task Purpose & Selected Entries

The purpose of this check is to document and execute a repeatable maintenance pass for selected entries in the **Animals** section of `README.md`.

Assigned Entries (Scoped strictly by URL):

| Entry URL | Display Name | Source Line | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|:---|
| `https://theaxolotlapi.netlify.app/` | Axolotl | Line 184 | No | Yes | No |
| `https://breedhealthscore.com/developers/` | Breed Health Score | Line 185 | No | Yes | No |
| `https://alexwohlbruck.github.io/cat-facts/` | Cat Facts | Line 186 | No | Yes | No |

Category Section Header: `### Animals` (Line 181 in root `README.md`)

### Disambiguation & URL Matching Policy
Line 187 of `README.md` contains another entry also named `Cat Facts` with the URL `https://catfact.ninja/`. The checker strictly matches entries by **URL**, never by display name, ensuring that line 186 (`https://alexwohlbruck.github.io/cat-facts/`) and line 187 are never confused or merged.

---

## 2. Repeatable Maintenance Report Structure

The checker generates a structured, reproducible JSON maintenance report clearly separating:

1. **Observed Facts:**
   - Raw probe results, HTTP response codes, response classification, documentation claims, and endpoint probes (verifying endpoint HTTPS behavior and CORS headers).
2. **Existing README Metadata:**
   - Current title, URL, description, Auth, HTTPS, and CORS fields parsed dynamically from `README.md`.
3. **Manual Verification Decisions:**
   - Evaluated decisions for Auth, HTTPS, CORS, and operational status, accompanied by explicit rationale, verified fields, and inconclusive fields.
4. **Recommended Metadata (Dynamic Comparison):**
   - Derived dynamically by comparing parsed existing metadata with verified reference evidence:
     - If verified evidence contradicts the README, an update is recommended and a discrepancy is recorded.
     - If existing metadata matches verified evidence, retaining the entry is recommended.
     - If evidence is inconclusive (e.g. Cat Facts CORS), the existing catalogue value is retained without claiming independent confirmation.
     - Discrepancy counts are derived dynamically from these field comparisons rather than hardcoded.
   - Entries are never automatically removed or modified.
5. **Evidence and Limitations:**
   - Authoritative documentation URLs, endpoint probes, and known transient limitations.

### Summary Metrics
The top-level `summary` object tracks pass metrics across evaluated entries:
- `total_evaluated`: Total number of selected entries evaluated.
- `retained_count`: Total number of entries whose overall recommended action is `retain`.
- `retained_unconfirmed_count`: Total number of entries retained where one or more fields are retained due to inconclusive evidence (`recommended_metadata.retained_unconfirmed` is non-empty).
- `updated_count`: Total number of entries requiring metadata updates.
- `operational_count`: Total entries whose verified operational status is `operational`.
- `transient_error_count`: Total entries encountering transient errors (e.g. HTTP 503).
- `discrepancies_detected`: Total number of field-level discrepancies between existing metadata and verified evidence.

---

## 3. Response Classifications & Policy for Inconclusive Results

The checker evaluates live or simulated responses using explicit, mutually exclusive categories:

- `successful_response`: Standard HTTP 2xx response.
- `redirect`: HTTP 3xx redirect response.
- `authentication_required`: HTTP 401 Unauthorized response or explicit requirement of credentials.
- `blocked_or_inconclusive`: HTTP 403 Forbidden, rate limiting (429), or anti-bot challenge (e.g. Cloudflare).
- `http_error`: HTTP 5xx server errors (e.g. 500, 502, 503).
- `timeout`: Network socket or connect timeout.
- `dns_failure`: Domain name resolution failure.

### Inconclusive & Transient Failure Policy
Per repository contribution standards and coursework instructions:
- A timeout, HTTP 403, Cloudflare challenge, HTTP 503 (e.g. sleeping Heroku dyno), or inaccessible documentation must **not** be interpreted as proof that an API is dead or discontinued.
- Catalogue entries must **not** be removed or altered solely due to isolated automated failures.
- `README.md` is modified only when reliable, conclusive evidence proves an existing catalogue field is inaccurate. If evidence is inconclusive, existing catalogue values are retained.

---

## 4. Findings & Maintenance Summary

1. **Axolotl (`https://theaxolotlapi.netlify.app/`):**
   - Landing page returns HTTP 200. Specification explicitly states no API key is required (`No`), HTTPS is supported (`Yes`), and CORS is not supported (`No`). Live probe confirms TLS/HTTPS enforcement on the API host.
   - Decision: `operational`, `retain` (no change).
2. **Breed Health Score (`https://breedhealthscore.com/developers/`):**
   - Developer documentation returns HTTP 200 and confirms no key or sign-up is required (`No`). Endpoint probe to `GET https://breedhealthscore.com/api/breeds.json` connects over HTTPS (`Yes`) and returns HTTP 200 JSON without `Access-Control-Allow-Origin` headers (`CORS: No`).
   - Decision: `operational`, `retain` (no change).
3. **Cat Facts (`https://alexwohlbruck.github.io/cat-facts/`):**
   - Documentation is active on GitHub Pages (HTTP 200) and describes unauthenticated `/facts`.
   - Direct probe of API backend `https://cat-fact.herokuapp.com/facts` connects over HTTPS with TLS encryption, proving endpoint HTTPS enforcement (`HTTPS: Yes`).
   - Backend Heroku router returned HTTP 503 (transient sleeping dyno), which does not constitute service discontinuation.
   - Because HTTP 503 did not establish CORS headers, CORS is treated as inconclusive rather than independently confirmed. The existing catalogue value (`CORS: No`) is retained without claiming independent verification.
   - Decision: `transient_http_error`, `retain` (no change). Cat Facts is counted in `retained_count` and also separately tracked under `retained_unconfirmed_count`.

---

## 5. Offline Fixtures

Fixtures are located under `tools/course_checks/fixtures/r02-t030/`:

1. `valid_entries.md`: Positive baseline of the Animals section containing the target URLs and the adjacent `catfact.ninja` entry.
2. `source_line_tracking.md`: Verifies exact source line preservation with preambles and blank lines.
3. `duplicate_url.md`: Tests duplicate URL detection within the category.
4. `missing_entry.md`: Tests detection of missing required target URLs.
5. `malformed_row.md`: Tests detection and reporting of table rows with invalid column counts.
6. `outside_category.md`: Verifies that selected URLs outside `### Animals` are ignored.
7. `url_matching_disambiguation.md`: Verifies URL-based matching when multiple entries share the display name `[Cat Facts]`.
8. `observed_facts_classification.json`: Exercises response classification across all 7 response types.
9. `recommendations_handling.json`: Validates recommendation actions and transient error handling.
10. `deterministic_report.json`: Validates deterministic, repeatable schema structure.

---

## 6. Usage & Verification Commands

### Run Deterministic Offline Self-Tests
```bash
python3 tools/course_checks/r02-t030.py --self-test
```

### Run Normal Checker Against Root README.md
```bash
python3 tools/course_checks/r02-t030.py
```

### Python Bytecode Compilation Check
```bash
python3 -m py_compile tools/course_checks/r02-t030.py
```

### Git Whitespace & Format Check
```bash
git diff --check
```
