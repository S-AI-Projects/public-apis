## Description
Adds an offline metadata validator for 5DollarFootball, AcesAPI and API-FOOTBALL, checking the catalogue's five-column table and required metadata fields.

## Related Issue / Fixes
Closes #55

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [ ] Catalogue correction

## Changes
- Added `tools/course_checks/r02-t055.py` with source-line-aware parsing and validation.
- Added a valid-row fixture and a missing-description rejection fixture.
- Added task README and evidence under `work/R02-T055/`.
- No catalogue correction was proposed without evidence.

## Screenshots
No screenshots; CLI checker.

## Testing
3 self-test checks passed locally on Python 3.15.2; py_compile, self-test and report exited 0. Three selected rows were found; malformed missing-description fixture was rejected. Offline; no live network.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T055/` evidence is retained for instructor review; it must not be included in a later upstream PR.