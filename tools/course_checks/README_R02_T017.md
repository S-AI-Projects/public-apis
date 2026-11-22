# Course Check Tool: R02-T017 (Classify Failures Correctly: Shopping)

## Overview
This tool performs robust HTTP status classification for catalogue entries in `Shopping` (`README.md`). It distinguishes between true success (200), missing resources (404), rate-limiting or anti-bot blocks (429/403), method fallbacks (HEAD-405 leading to GET-200), transient timeouts, and DNS failures.

## Selected Entries
1. **ARC**
   - URL: `https://www.arcreport.ai/developers`
   - Category: `Shopping`
   - Line: 2249
2. **Best Buy**
   - URL: `https://bestbuyapis.github.io/api-documentation/#overview`
   - Category: `Shopping`
   - Line: 2250
3. **BirkinBagStock**
   - URL: `https://birkinbagstock.com/.well-known/openapi.json`
   - Category: `Shopping`
   - Line: 2251

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t017.py --self-test
  ```
- Run live HTTP probe with GET fallback:
  ```bash
  python3 tools/course_checks/r02-t017.py --live
  ```

## Acceptance Criteria
- [x] Fixtures for 200, 404, 429, HEAD-405/GET-200, timeout, and DNS failure produce 6 distinct labels.
- [x] Only a manually confirmed missing resource (404) is recommended for removal.
- [x] Self-test exits non-zero on assertion failures.
- [x] Retention policy strictly enforced across all non-404 conditions.
