## Description
This pull request implements the duplicate-URL checker tool for Task R02-T052 (2 of 10) targeting the `### Anti-Malware` section of `README.md`. It performs conservative normalization matching (scheme/host lowercase, default ports removal, trailing slash removal on path, bare host normalization) while strictly keeping distinct URLs differing in query strings (including UTM parameters), fragments/anchors, path casing, or protocol scheme (HTTP vs HTTPS).

The checker was verified against:
1. The three selected entries in `Anti-Malware`:
   - AbuseIPDB (`https://docs.abuseipdb.com/`, line 244)
   - AlienVault Open Threat Exchange (OTX) (`https://otx.alienvault.com/api`, line 245)
   - CAPEsandbox (`https://capev2.readthedocs.io/en/latest/usage/api.html`, line 246)
2. The entire `### Anti-Malware` section (17 total entries across lines 241-260).

All documentation URLs are active and distinct, and CORS response headers were not directly observed (retaining `Unknown` in `README.md` as safe and accurate). Consequently, `README.md` is left unchanged.

## Related Issue
Fixes: #52

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
- Created `tools/course_checks/r02-t052.py`: CLI tool implementing conservative URL normalization, exact matching, distinction reasoning, review-pair validation guardrails, and fixture/negative self-testing.
- Created `tools/course_checks/README-r02-t052.md`: Documentation covering tool usage, conservative normalization rules, distinction rules, and review-pair schema.
- Created `tools/course_checks/fixtures/r02-t052/`: 10 comprehensive JSON fixtures covering exact matches, conservative normalization (trailing slash, default port, host case), kept-distinct cases (query strings, fragments, UTM parameters, scheme differences), no-duplicate lists, and rejection of unreviewed proposed deletions.
- Created `work/R02-T052/`: Evidence directory containing tool versions, inputs, manual verification notes, full section reports (`report_full_section.txt`, `report_full_section.json`), expected vs actual comparisons, self-test output logs, and reviewed pairs documentation.
- Left `README.md` untouched because all documentation links are canonical, distinct, and CORS remains `Unknown` (safe unverified state).

## Screenshots / Recordings
N/A

## Testing
- Command: `python3 tools/course_checks/r02-t052.py --self-test`
  - Results: Ran 10 offline JSON fixtures covering all duplicate and distinct cases; all passed. Ran internal negative test verifying non-zero exit code on wrong expectations.
  - Exit Code: `0`
- Command: `python3 tools/course_checks/r02-t052.py --run-negative-test-case`
  - Results: Deliberately failing assertion triggered as expected.
  - Exit Code: `3`
- Command: `python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware --selected-only`
  - Results: Successfully parsed `README.md` dynamically at lines 244-246, found 0 duplicate groups, confirmed 3 distinct entries.
  - Exit Code: `0`
- Command: `python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware`
  - Results: Successfully analyzed all 17 entries in `### Anti-Malware` (lines 244-260), found 0 duplicate groups, output saved in `report_full_section.txt` and `report_full_section.json`.
  - Exit Code: `0`

## Checklist
- [x] I have tested my changes locally.
- [x] I have added or updated tests, if needed.
- [x] I have updated documentation, if needed.
- [x] I have followed the project's coding guidelines.
- [x] I have run the relevant tests and checks.
- [ ] I have addressed previous review feedback, if applicable. (N/A, first submission)

## Additional Notes
- Targets the S-AI-Projects fork only (`student/e26b07f0662/R02-T052`).
- The `work/R02-T052/` folder is for the fork PR only and must be removed from any later upstream branch.
- No link was removed or altered because of an automated request failure. All entries were verified to be active and canonical.
