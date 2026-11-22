# Course Check Tool: R02-T013 (Detect Probable Duplicates: Phone)

## Overview
This tool performs exact duplicate detection and conservative URL normalization grouping across the Public APIs catalogue, specifically targeting the `Phone` category. It guarantees that query parameters (e.g. campaign tokens) and specific fragment anchors are preserved, ensuring distinct endpoints are not falsely merged.

## Selected Entries
1. **Numlookup**
   - URL: `https://numlookupapi.com`
   - Category: `Phone`
   - Line: 2040
2. **Numverify**
   - URL: `https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers`
   - Category: `Phone`
   - Line: 2041
3. **Cloudmersive Validate**
   - URL: `https://cloudmersive.com/phone-number-validation-API`
   - Category: `Phone`
   - Line: 2042

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t013.py --self-test
  ```
- Inspect selected entries:
  ```bash
  python3 tools/course_checks/r02-t013.py --check-selected
  ```

## Acceptance Criteria
- [x] Exact duplicates are detected.
- [x] Distinct anchors and query-dependent resources are not automatically merged.
- [x] Every proposed deletion requires a manually reviewed pair.
- [x] Checker has a `--self-test` mode with non-zero exit on assertion failures.
- [x] No link is removed solely because a single automated request failed.
