## Description
Adds a structured parser for Aftership, Correios and Mapbox, retaining display name, URL, category, metadata and source line.

## Related Issue / Fixes
Closes #59

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [ ] Catalogue correction

## Changes
- Added `tools/course_checks/r02-t059.py` with section-scoped extraction and source-line metadata.
- Added fixture checks that ignore fenced fake links and preserve URL fragments.
- Added task README and evidence under `work/R02-T059/`.
- No catalogue correction was needed.

## Screenshots
No screenshots; CLI checker.

## Testing
4 self-test checks passed locally on Python 3.15.2; py_compile, self-test and report exited 0. All three selected entries found, fenced fake ignored, fragment preserved. Offline.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T059/` evidence is retained for instructor review; it must not be included in a later upstream PR.