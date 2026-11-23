## Description
Adds a scoped formatting and ordering checker for AI Economics Tools, AI For Thai and AI Stupid Level.

## Related Issue / Fixes
Closes #57

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [ ] Catalogue correction

## Changes
- Added `tools/course_checks/r02-t057.py` with Markdown table validation, source lines, alphabetical-order checks and fenced-code exclusion.
- Added fixtures covering malformed rows and Thai Unicode.
- Added task README and evidence under `work/R02-T057/`.
- No catalogue correction was needed.

## Screenshots
No screenshots; CLI checker.

## Testing
5 self-test checks passed locally on Python 3.15.2; py_compile, self-test and report exited 0. Malformed row rejected, fenced fake ignored, Thai Unicode preserved, all three entries found. Offline.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T057/` evidence is retained for instructor review; it must not be included in a later upstream PR.