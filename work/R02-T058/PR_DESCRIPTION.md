## Description
Documents access requirements for Chinese Character Web, Chinese Text Project and Collins without storing credentials or asserting unverified access claims.

## Related Issue / Fixes
Closes #58

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [ ] Catalogue correction

## Changes
- Added `tools/course_checks/r02-t058.py` with source-line-aware access report.
- Chinese Character Web remains explicitly unverified; Chinese Text Project access is described as tiered; Collins key/registration and published tiers are documented with official references.
- Added task README and evidence under `work/R02-T058/`.

## Screenshots
No screenshots; CLI checker and evidence report.

## Testing
5 self-test checks passed locally on Python 3.15.2; py_compile, self-test and report exited 0. Three selected entries reported; no credentials stored. Offline.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T058/` evidence is retained for instructor review; it must not be included in a later upstream PR.