# Course Check Tool: R02-T015 (Verify Entry Metadata: Test Data)

## Overview
This tool parses and verifies entry metadata for the `Test Data` section in `README.md`. It validates each required column (API, Description, Auth, HTTPS, CORS) against schema constraints, rejects incomplete or malformed entries, and generates a structured evidence table comparing observed documentation with catalogue values.

## Selected Entries
1. **AddressMock**
   - URL: `https://addressmock.com/api`
   - Category: `Test Data`
   - Line: 2430
2. **Bacon Ipsum**
   - URL: `https://baconipsum.com/json-api/`
   - Category: `Test Data`
   - Line: 2431
3. **Dicebear Avatars**
   - URL: `https://avatars.dicebear.com/`
   - Category: `Test Data`
   - Line: 2432

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t015.py --self-test
  ```
- Generate metadata evidence table:
  ```bash
  python3 tools/course_checks/r02-t015.py --evidence-table
  ```

## Acceptance Criteria
- [x] Fixture with missing required field fails validation.
- [x] Evidence table provides source URL, observed value, and proposed value for each change.
- [x] Checker has `--self-test` mode exiting non-zero on assertion failure.
- [x] Retention policy enforced: AddressMock is retained pending manual review.
