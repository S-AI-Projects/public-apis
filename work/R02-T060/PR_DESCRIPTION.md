## Description
Adds a repeatable, offline maintenance report for AniAPI, AniDB and AniList, including source lines, before/after metadata, manual decisions and recommendations.

## Related Issue / Fixes
Closes #60

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [ ] Catalogue correction

## Changes
- Added `tools/course_checks/r02-t060.py` for a scoped Anime report.
- Added repeat-run fixture checks for deterministic output and before/after metadata.
- Added task README and evidence under `work/R02-T060/`.
- No catalogue change was proposed without official-source evidence.

## Screenshots
No screenshots; CLI checker.

## Testing
3 self-test checks passed locally on Python 3.15.2; py_compile, self-test and report exited 0. Repeated output was identical and all three entries were included. Offline.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T060/` evidence is retained for instructor review; it must not be included in a later upstream PR.