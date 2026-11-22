# R02-T052 Results Table: Expected vs Actual

**Task**: R02-T052 (duplicate-URL check)  
**Related Issue**: Fixes #52 (`Divyanshi Yadav — R02-T052: Detect probable duplicates: Anti-Malware [README.md]`)  
**Target Section**: `### Anti-Malware` in `README.md`  
**Execution Date**: 2026-11-22  
**Tool**: `tools/course_checks/r02-t052.py`  

## Selected Entries Under Evaluation

| Line | Entry Name | URL in README | Normalized URL | Auth | HTTPS | CORS Observed | CORS in README |
|:---|:---|:---|:---|:---|:---|:---|:---|
| 244 | AbuseIPDB | `https://docs.abuseipdb.com/` | `https://docs.abuseipdb.com` | `apiKey` | Yes | NOT OBSERVED | Unknown |
| 245 | AlienVault Open Threat Exchange (OTX) | `https://otx.alienvault.com/api` | `https://otx.alienvault.com/api` | `apiKey` | Yes | NOT OBSERVED | Unknown |
| 246 | CAPEsandbox | `https://capev2.readthedocs.io/en/latest/usage/api.html` | `https://capev2.readthedocs.io/en/latest/usage/api.html` | `apiKey` | Yes | NOT OBSERVED | Unknown |

## Comparison: Expected vs Actual (Selected Run & Full-Section Run)

| Metric / Check | Expected | Actual | Status | Notes |
|:---|:---|:---|:---|:---|
| **Selected Run: Duplicates** | 0 groups | 0 groups | PASS | All 3 selected entries resolve to distinct endpoints |
| **Selected Run: Distinct** | 3 entries | 3 entries | PASS | Lines 244, 245, 246 differ by hostname |
| **Lines 244 vs 245** | `hostname_differs` | `hostname_differs` | PASS | `docs.abuseipdb.com` vs `otx.alienvault.com` |
| **Lines 244 vs 246** | `hostname_differs` | `hostname_differs` | PASS | `docs.abuseipdb.com` vs `capev2.readthedocs.io` |
| **Lines 245 vs 246** | `hostname_differs` | `hostname_differs` | PASS | `otx.alienvault.com` vs `capev2.readthedocs.io` |
| **Full Section: Duplicates** | 0 groups | 0 groups | PASS | 17 total entries analyzed; 0 duplicate groups found |
| **Full Section: Distinct** | 17 entries | 17 entries | PASS | Verified in `report_full_section.txt` and `.json` |
| **Proposed Deletions** | None | None | PASS | No deletions proposed or recommended |
| **Self-Test Suite** | 10/10 PASS | 10/10 PASS | PASS | All 10 edge cases and negative test passed |
| **Negative Test Exit** | Non-zero (3) | Non-zero (3) | PASS | Deliberate wrong expectation caught |
| **README Action** | No change | No change | PASS | All URLs active; CORS unverified (Unknown retained) |
