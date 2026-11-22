# Course Check Tool: R02-T019 (Document Repeatable Maintenance Pass: Books)

## Overview
This tool generates a one-command repeatable maintenance pass report for catalogue entries in `Books` (`README.md`). The report details before/after metadata, strictly separates observed factual status from manual recommendations, and produces deterministic, reproducible output across runs.

## Selected Entries
1. **A Bíblia Digital**
   - URL: `https://www.abibliadigital.com.br/en`
   - Category: `Books`
   - Line: 344
2. **Amanah Sunnah**
   - URL: `https://sunnah.amanahagent.cloud/developers`
   - Category: `Books`
   - Line: 345
3. **Bhagavad Gita**
   - URL: `https://docs.bhagavadgitaapi.in`
   - Category: `Books`
   - Line: 346

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t019.py --self-test
  ```
- Generate formatted maintenance report:
  ```bash
  python3 tools/course_checks/r02-t019.py --report
  ```

## Acceptance Criteria
- [x] Report names exact source lines (L344, L345, L346).
- [x] Separates observed facts from recommendations.
- [x] Produces stable, deterministic output from identical inputs.
- [x] Self-test exits non-zero on assertion failures.
- [x] Retention policy enforced for transient 503 errors.
