# Course Checkers

## R02-T025 — Verify Entry Metadata — Social

This checker verifies catalogue metadata fields (`Auth`, `HTTPS`, `CORS`, `Description`, `URL`) for three assigned entries in the `Social` category against official documentation and live headers.

### Selected README entries

| API | README line | Listed URL | Description | Auth | HTTPS | CORS |
|---|---:|---|---|---|---|---|
| 4chan | 2289 | https://github.com/4chan/4chan-API | Simple image-based bulletin board dedicated to a variety of topics | No | Yes | Yes |
| API Direct | 2290 | https://apidirect.io/docs | Real-time social media data from X, LinkedIn, Reddit, YouTube, Instagram, TikTok, Facebook and news | `apiKey` | Yes | Yes |
| Ayrshare | 2291 | https://www.ayrshare.com | Social media APIs to post, get analytics, and manage multiple users social media accounts | `apiKey` | Yes | Yes |

### Official metadata verification

1. **4chan**
   - **Documentation:** https://github.com/4chan/4chan-API
   - **Auth:** `No`. The API is a public read-only JSON interface requiring no authentication.
   - **HTTPS:** `Yes`. Data is served over TLS via `https://a.4cdn.org/`.
   - **CORS:** `Yes`. The official documentation explicitly states: `[CORS] is supported from origins boards.4chan.org or boards.4channel.org, via http:// or https://.` Restricted allowed origins do not mean CORS is unsupported; the API actively supports and implements CORS headers for its explicitly allowed origins rather than arbitrary external origins. In accordance with `CONTRIBUTING.md` (`Yes = the API supports CORS`), the catalogue value `Yes` is correct.

2. **API Direct**
   - **Documentation:** https://apidirect.io/docs
   - **Auth:** `apiKey`. Endpoints authenticate via the `X-API-Key` request header.
   - **HTTPS:** `Yes`. All endpoints use TLS (`https://apidirect.io/`).
   - **CORS:** `Yes`. The API responds to cross-origin requests with `Access-Control-Allow-Origin: <origin>`, supporting browser client calls.

3. **Ayrshare**
   - **Documentation:** https://www.ayrshare.com and https://www.ayrshare.com/docs
   - **Auth:** `apiKey`. Endpoints authenticate using `Authorization: Bearer <API_KEY>`.
   - **HTTPS:** `Yes`. All API requests use TLS (`https://api.ayrshare.com/`).
   - **CORS:** `Yes`. The API responds with `Access-Control-Allow-Origin: <origin>`, permitting browser-based cross-origin calls.

### Catalogue metadata corrections

No modifications were required for root `README.md`. All three assigned entries (`4chan`, `API Direct`, and `Ayrshare`) possess verified and accurate metadata conforming to `CONTRIBUTING.md` standards.

### Running the checker

From the repository root:

```bash
# Run deterministic offline self-tests against fixtures and README.md
python3 tools/course_checks/r02-t025.py --self-test

# Run verification and export evidence to work/R02-T025/
python3 tools/course_checks/r02-t025.py
```

### Fixtures

Offline fixtures are stored under `tools/course_checks/fixtures/r02-t025/`:
- `valid_entries.md`: Baseline fixture with all three entries valid and matching verified metadata.
- `missing_required_field.md`: Negative test case where a required table column (CORS) is missing (< 5 columns).
- `extra_column.md`: Negative test case where an entry row contains an extra column (> 5 columns).
- `incorrect_metadata.md`: Negative test case with mismatched metadata values (Auth, HTTPS).
- `invalid_field_value.md`: Negative test case with non-standard enum values.
- `line_tracking.md`: Tests precise preservation of line numbers across document layouts.

### Evidence

Local evidence is stored in `work/R02-T025/` (untracked):
- `actual.json`: Current checker validation report.
- `expected.json`: Ground truth reference metadata.
- `verification-notes.md`: Detailed official documentation notes and citations.
- `parsed-entries.json`: Parsed catalogue entries with source line numbers.
- `tool-versions.txt`: Tool and environment version information.
