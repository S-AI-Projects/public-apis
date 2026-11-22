The implementation for Task R02-T052 (Issue #52) is complete.

All requirements have been met:
- Implemented `tools/course_checks/r02-t052.py` with conservative URL normalization, exact matching, distinct URL rules, and manual review guardrails.
- Added 10 comprehensive offline fixtures in `tools/course_checks/fixtures/r02-t052/`.
- Verified that `--self-test` passes all fixtures (exit code 0) and includes an integrated negative test (exit code 3).
- Added tool documentation in `tools/course_checks/README-r02-t052.md`.
- Evaluated the three selected entries (AbuseIPDB, AlienVault OTX, CAPEsandbox) as well as the full `### Anti-Malware` section (17 entries) and verified no duplicate URLs exist.
- Generated all evidence and verification records in `work/R02-T052/`.

Pull Request: <PR LINK>

Please review the PR.
