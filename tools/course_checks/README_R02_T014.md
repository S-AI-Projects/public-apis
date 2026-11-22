# Course Check Tool: R02-T014 (Check Category Placement: Security)

## Overview
This tool verifies category placement and structural integrity in `README.md`, focusing on the `Security` section. It flags duplicate category headers and identifies misplaced entries based on the resource's actual subject matter rather than simple keyword heuristics.

## Selected Entries
1. **Agent Verifier**
   - URL: `https://packet.guru/agents/reference`
   - Category: `Security`
   - Line: 2180
   - Subject: Web bot authentication signatures and agent identity
2. **Application Environment Verification**
   - URL: `https://github.com/fingerprintjs/aev`
   - Category: `Security`
   - Line: 2181
   - Subject: Device safety, Android root detection, integrity risks
3. **BinaryEdge**
   - URL: `https://docs.binaryedge.io/api-v2.html`
   - Category: `Security`
   - Line: 2182
   - Subject: Threat scanning and internet-wide vulnerability intelligence

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t014.py --self-test
  ```
- Check selected Security entries:
  ```bash
  python3 tools/course_checks/r02-t014.py --check-selected
  ```

## Acceptance Criteria
- [x] Deliberately misplaced fixtures identified with resource subject cited.
- [x] Valid categories preserved without reclassification from ambiguous keywords.
- [x] Duplicate headings flagged.
- [x] Self-test exits non-zero on assertion failure.
- [x] No link removed solely due to automated check failures.
