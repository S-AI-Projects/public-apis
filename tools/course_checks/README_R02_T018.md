# Course Check Tool: R02-T018 (Explain Access Requirements: Text Analysis)

## Overview
This tool audits and verifies access and authentication requirements for catalogue entries in `Text Analysis` (`README.md`). It ensures all access claims cite official documentation, ensures zero credentials or secrets are stored, and guarantees that temporarily unreachable endpoints are labeled `unverified` rather than `free` or `broken`.

## Selected Entries
1. **Code Detection**
   - URL: `https://codedetectionapi.runtime.dev`
   - Category: `Text Analysis`
   - Line: 2474
   - Status: Labeled `unverified` (TLS handshake failure on host during probe)
2. **apilayer languagelayer**
   - URL: `https://languagelayer.com/`
   - Category: `Text Analysis`
   - Line: 2475
   - Citation: `https://languagelayer.com/documentation`
   - Access Model: Registration required, uses API Access Key (`apiKey`); proposed catalogue correction from `OAuth` to `apiKey`.
3. **Aylien Text Analysis**
   - URL: `https://docs.aylien.com/textapi/#getting-started`
   - Category: `Text Analysis`
   - Line: 2476
   - Status: Labeled `unverified` (legacy endpoint unreachable via DNS)

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t018.py --self-test
  ```
- Run access requirements audit:
  ```bash
  python3 tools/course_checks/r02-t018.py --audit
  ```

## Acceptance Criteria
- [x] Each access claim cites the official resource.
- [x] No credentials saved.
- [x] Unavailable resources labeled `unverified` rather than free or broken.
- [x] Self-test exits non-zero on assertion failures.
- [x] Retention policy enforced: No links removed solely on automated request failure.
