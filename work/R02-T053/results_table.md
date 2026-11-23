# Results Table: Task R02-T053

## Selected Entries Evaluation (`### Phone`, lines 2037–2048)

| Line | Entry Name | URL | Current Category | Cited Subject | Recommendation | Status |
|---|---|---|---|---|---|---|
| **2040** | Numlookup | `https://numlookupapi.com` | `Phone` | `phone number validation and carrier lookup` | `keep` | Aligned |
| **2041** | Numverify | `https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers` | `Phone` | `phone number validation` | `keep` | Aligned |
| **2042** | Cloudmersive Validate | `https://cloudmersive.com/phone-number-validation-API` | `Phone` | `validate and standardize phone numbers` | `keep` | Aligned |

## Document-Wide Heading Check Results (README.md)

- **Total Headings Inspected**: 59
- **Repeated Headings Found**: 0
- **Misplaced Category Headings Found**: 0

## Offline Fixtures & Test Results

| Fixture | Description | Expected Status | Actual Status | Result |
|---|---|---|---|---|
| `fixture_01` | Valid entry under Phone with cited subject | `PASS` (`keep`) | `PASS` (`keep`) | ✅ PASS |
| `fixture_02` | Misplaced entry (WeatherAPI under Animals) | `FLAGGED` (`manual_review`) | `FLAGGED` (`manual_review`) | ✅ PASS |
| `fixture_03` | Repeated heading detection | `HEADING_ISSUES` | `HEADING_ISSUES` | ✅ PASS |
| `fixture_04` | Misplaced heading detection | `HEADING_ISSUES` | `HEADING_ISSUES` | ✅ PASS |
| `fixture_05` | Keyword lookalike (no citation) | `PASS` (`keep`) | `PASS` (`keep`) | ✅ PASS |
| `fixture_06` | Proposed move without citation | `REJECTED` | `REJECTED` | ✅ PASS |
| `fixture_07` | Proposed move with valid citation | `ACCEPTED_RECOMMENDATION` | `ACCEPTED_RECOMMENDATION` | ✅ PASS |
| `negative_test` | Subprocess intentional assertion test | Exit code `3` | Exit code `3` | ✅ PASS |
