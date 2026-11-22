# Course Check Tool: R02-T016 (Make Checks Work Offline: Food & Drink)

## Overview
This tool provides a fixture-based offline validation test suite for parsing and validating the `Food & Drink` section of `README.md`. It guarantees that validation can run completely disconnected from the network, with explicit expected outcomes for valid rows, malformed rows, and unusual URL characters.

## Selected Entries
1. **BaconMockup**
   - URL: `https://baconmockup.com/`
   - Category: `Food & Drink`
   - Line: 1220
2. **CalorieNinjas**
   - URL: `https://calorieninjas.com/api`
   - Category: `Food & Drink`
   - Line: 1221
3. **Chomp**
   - URL: `https://chompthis.com/api/`
   - Category: `Food & Drink`
   - Line: 1222

## Usage
- Run offline self-test assertions (guaranteed network-isolated):
  ```bash
  python3 tools/course_checks/r02-t016.py --self-test
  ```
- Optional live check:
  ```bash
  python3 tools/course_checks/r02-t016.py --live
  ```

## Acceptance Criteria
- [x] Suite passes with network access disabled (socket access blocked).
- [x] Explicit expected outcomes for valid rows, malformed rows, and unusual URL characters.
- [x] Self-test exits non-zero on assertion failures.
- [x] Retention policy enforced: Live checks do not remove links solely on single request failure.
