## Description
Adds a fixture-based offline parser and validator for Marketstack, Aletheia and Alpaca. Corrects the two Finance table rows that had an extra empty cell.

## Related Issue / Fixes
Closes #56

## Type
- [x] Tooling / automated checks
- [x] Documentation and coursework evidence
- [x] Evidence-backed catalogue formatting correction

## Changes
- Added `tools/course_checks/r02-t056.py` with five-column parsing, validation, source-line reporting and non-zero report failure for missing/invalid targets.
- Corrected Aletheia and Alpaca table formatting in `README.md`.
- Added task README and evidence under `work/R02-T056/`.

## Screenshots
No screenshots; CLI checker and Markdown table correction.

## Testing
4 self-tests passed locally on Python 3.15.2. py_compile, self-test and report exited 0; all three Finance entries valid, no missing or invalid targets; query-string characters preserved. Offline; no network.

## Checklist
- [x] Focused on the assigned category and selected entries.
- [x] Offline self-test included; failed assertions exit non-zero.
- [x] Source lines, source URLs and evidence recorded.
- [x] No link removed solely due to a single automated request failure.
- [x] All task changes squashed into one commit.
- [x] Follows the repository contribution guide and table schema where applicable.
- [x] No unrelated changes.

## Additional Notes
Coursework PR to the S-AI-Projects organisation fork only. The `work/R02-T056/` evidence is retained for instructor review; it must not be included in a later upstream PR.