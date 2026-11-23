## Description
This pull request implements the category-consistency and heading placement checker for Task R02-T053 (Issue #53) targeting the `### Phone` section of `README.md` (lines 2037–2048).

The tool performs dynamic Markdown parsing to verify heading structure, detect duplicate or misplaced category headings across the document, and enforce category consistency guardrails:
- Forbids keyword-only reclassification (names or descriptions containing generic words like "Validation" or "Data" are never moved based on keywords).
- Requires an explicit, verified subject citation from official documentation (`observed_subject`, `citation_url`, `observation_date`) for any proposed move or misplacement flag.
- Enforces conservative recommendation outputs (`keep`, `manual_review` with `proposed_category`, or rejecting uncited proposals). Automated edits and link removals are strictly prohibited.

The checker was evaluated against:
1. The three selected entries in `### Phone`:
   - Numlookup (`https://numlookupapi.com`, line 2040)
   - Numverify (`https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers`, line 2041)
   - Cloudmersive Validate (`https://cloudmersive.com/phone-number-validation-API`, line 2042)
2. All 8 entries in `### Phone` (lines 2040–2047).
3. All 59 markdown headings across `README.md`.

All three documentation pages were inspected sequentially using the sandboxed browser agent. All three have a primary, stated subject of phone number validation, carrier lookup, and international phone formatting, aligning squarely with `### Phone`. Existing Auth and CORS values in `README.md` (specifically Cloudmersive's Auth `apiKey` / CORS `Yes`, and Numlookup / Numverify CORS `Unknown`) were unverified via direct page text inspection (marked NOT OBSERVED). Because there is no direct observed evidence contradicting the existing entries, and category placement is fully compliant with `CONTRIBUTING.md`, `README.md` is left unchanged.

## Related Issue
Fixes: #53

## Type of Change
- [ ] Bug Fix
- [x] New Feature
- [ ] UI/UX Improvement
- [ ] Performance Improvement
- [x] Tests
- [x] Documentation
- [ ] Refactoring / Maintenance
- [ ] CI/CD

## Changes Made
- Created `tools/course_checks/r02-t053.py`: Standalone CLI tool implementing dynamic Markdown parsing, heading consistency checks (repeated & alphabetical ordering), citation validation, keyword-reclassification guardrails, offline fixture testing, and negative test subprocess assertion.
- Created `tools/course_checks/README-r02-t053.md`: Comprehensive documentation covering category rules, what counts as a flag, citation schema, subject-to-category mapping, and CLI usage.
- Created `tools/course_checks/fixtures/r02-t053/`: 7 offline JSON fixtures validating valid entries, misplaced entries with citations, repeated headings, misplaced headings, keyword lookalikes, rejected uncited moves, and accepted cited move recommendations.
- Created `work/R02-T053/`: Evidence directory containing inputs, tool versions, manual verification notes, full section reports (`report_full_section.txt`, `report_full_section.json`), selected reports (`report_selected.txt`, `report_selected.json`), self-test transcript, and comparison tables.
- Left `README.md` unchanged in accordance with evidence honesty principles.

## Screenshots / Recordings
N/A

## Testing
- Command: `python3 tools/course_checks/r02-t053.py --self-test`
  - Results: Executed 7 offline JSON fixtures in memory; all passed. Subprocess negative test executed and exited with non-zero code 3 as asserted.
  - Exit Code: `0`
- Command: `python3 tools/course_checks/r02-t053.py --negative-test`
  - Results: Standalone execution triggered intentional assertion failure on uncited proposal.
  - Exit Code: `3`
- Command: `python3 tools/course_checks/r02-t053.py --readme README.md --section Phone --selected-only --citations work/R02-T053/citations.json`
  - Results: Evaluated lines 2040–2042; confirmed 0 repeated headings, 0 misplaced headings, and 3 entries aligned with `Phone` (`keep`).
  - Exit Code: `0`
- Command: `python3 tools/course_checks/r02-t053.py --readme README.md --section Phone --citations work/R02-T053/citations.json`
  - Results: Evaluated all 8 entries in `### Phone` and whole document headings; confirmed 0 repeated headings, 0 misplaced headings.
  - Exit Code: `0`

## Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [ ] I have addressed previous review feedback, if applicable. (N/A, first submission)

## Additional Notes
- This pull request targets the `S-AI-Projects/public-apis` fork repository only.
- The `work/R02-T053/` directory contains task evidence and must be removed prior to any future upstream merge.
- No link is removed or altered due to a single unverified attribute or failed request.
- NOT OBSERVED items: CORS response headers for Numlookup, Numverify, and Cloudmersive Validate, as well as Cloudmersive's Auth method (not displayed on its landing page). Manual verification steps are provided in `work/R02-T053/manual_verification.md`.
