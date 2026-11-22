# Course Check Tool: R02-T012 (Verify Redirects: Open Data)

## Overview
This tool verifies URL redirect chains with a bounded request budget for entries in the `Open Data` section of `README.md`. It distinguishes between direct healthy resources, permanent redirects, redirect loops, transient timeouts, and login walls.

## Selected Entries
1. **10ML Fragrance Index**
   - URL: `https://mcp.10ml.com/openapi.json`
   - Category: `Open Data`
   - Line: 1887
2. **221**
   - URL: `https://221.orvlabs.com/documentation`
   - Category: `Open Data`
   - Line: 1888
3. **49 Gallery Historical Data**
   - URL: `https://api.181649.com/docs`
   - Category: `Open Data`
   - Line: 1889

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t012.py --self-test
  ```
- Run live check on selected entries:
  ```bash
  python3 tools/course_checks/r02-t012.py --live
  ```

## Acceptance Criteria
- [x] Offline 200, 301->200, redirect-loop, and timeout fixtures classified correctly.
- [x] Live recommendation records final official URL and observation date.
- [x] Self-test exits non-zero on failing assertions.
- [x] Link retention policy enforced: No link is removed solely due to automated check failures.
