# Manual Verification & Evidence: Task R02-T053

This document records the exact observations from inspecting the three official documentation pages using the sandboxed browser agent on 2026-11-23, along with unverified properties marked **NOT OBSERVED** and instructions for manual verification.

Existing README Auth and CORS values for all three entries are **unverified, left unchanged** because there is no direct, observed proof that any existing value is wrong.

---

## 1. Numlookup

- **README Entry**: Line 2040: `| [Numlookup](https://numlookupapi.com) | Phone number validation and carrier lookup API with global coverage | `apiKey` | Yes | Unknown |`
- **Target URL**: `https://numlookupapi.com`
- **Effective URL**: `https://numlookupapi.com/` (HTTPS: Yes)
- **Observed Headline / Hero**: *"Phone Number Lookup & Validation API"* / *"Check whether a phone number is real, which carrier it belongs to and whether it's mobile, landline or VoIP, with one API call."*
- **Observed Page Title**: `Number Lookup API: Free Phone Validation & Carrier Lookup`
- **Observed Stated Subject**: Phone number lookup, validation, carrier detection, line type (mobile/landline/VoIP), reverse phone lookup, HLR lookup across 230+ countries.
- **Observed Auth**: API key passed via header (`apikey: YOUR-APIKEY` shown in sample cURL request).
- **CORS Status**: **NOT OBSERVED**. (CORS response headers are not stated or displayed in visible page text).
  - *Manual Verification Step*: Execute `curl -I -H "Origin: https://example.com" https://api.numlookupapi.com/v1/validate/+12069220880` and inspect `Access-Control-Allow-Origin`.
- **Bot Detection / CAPTCHA**: None encountered.
- **Category Assessment**: Primary subject is phone numbers; aligns with `### Phone`.

---

## 2. Numverify

- **README Entry**: Line 2041: `| [Numverify](https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers) | Phone number validation | `apiKey` | Yes | Unknown |`
- **Target URL**: `https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers`
- **Effective URL**: `https://numverify.com/?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers` (HTTPS: Yes; UTM parameters preserved)
- **Observed Headline / Hero**: *"Global Phone Number Validation & Lookup JSON API"* / *"Real-time REST API supporting 232 countries"*
- **Observed Page Title**: `Numverify API | Phone Number Validation & Phone Lookup API`
- **Observed Stated Subject**: Global phone number validation, formatting, carrier detection, and line type lookup via JSON API.
- **Observed Auth**: API key (stated in APILayer unified suite banner: *"One account, one API key, one dashboard, one bill"*).
- **CORS Status**: **NOT OBSERVED**. (CORS response headers not observable in page content).
  - *Manual Verification Step*: Send a CORS preflight or GET request with an `Origin` header (`curl -I -H "Origin: https://example.com" http://apilayer.net/api/validate`) and inspect the response headers.
- **Bot Detection / CAPTCHA**: None encountered.
- **Category Assessment**: Primary subject is phone numbers; aligns with `### Phone`.

---

## 3. Cloudmersive Validate

- **README Entry**: Line 2042: `| [Cloudmersive Validate](https://cloudmersive.com/phone-number-validation-API) | Validate international phone numbers | `apiKey` | Yes | Yes |`
- **Target URL**: `https://cloudmersive.com/phone-number-validation-API`
- **Effective URL**: `https://cloudmersive.com/phone-number-validation-API` (HTTPS: Yes)
- **Observed Headline / Hero**: *"Validate and Standardize Phone Numbers"* / *"Enable your systems to instantly check phone numbers upon user input to both auto-validate at point of entry and retrieve its location information."*
- **Observed Page Title**: `Phone Number Validation API - Cloudmersive APIs`
- **Observed Stated Subject**: International phone number validation, parsing, standardization (E.164), and location retrieval.
- **Observed Auth**: **NOT OBSERVED**. (The documentation page content does not visibly state the authentication method or header parameters).
  - *Manual Verification Step*: Log in to Cloudmersive developer portal or API reference docs to confirm header (`Apikey`).
- **CORS Status**: **NOT OBSERVED**. (CORS response headers not observable in page content).
  - *Manual Verification Step*: Send an OPTIONS/GET request from a browser or curl (`curl -I -X OPTIONS -H "Origin: https://example.com" -H "Access-Control-Request-Method: POST" https://api.cloudmersive.com/validate/phonenumber/basic`) to test `Access-Control-Allow-Origin`.
- **Bot Detection / CAPTCHA**: None encountered.
- **Category Assessment**: Primary subject is phone numbers; aligns with `### Phone`.

---

## Unverified Status Summary

| Entry | Field | README Value | Observed Status | Action Taken |
|---|---|---|---|---|
| Numlookup | CORS | `Unknown` | NOT OBSERVED | Unverified, left unchanged |
| Numverify | CORS | `Unknown` | NOT OBSERVED | Unverified, left unchanged |
| Cloudmersive Validate | Auth | `` `apiKey` `` | NOT OBSERVED | Unverified, left unchanged |
| Cloudmersive Validate | CORS | `Yes` | NOT OBSERVED | Unverified, left unchanged |

Existing Auth and CORS values for all three entries are **unverified, left unchanged** because there is no direct, observed proof that any existing value is wrong. Because all three APIs squarely belong in `### Phone`, **no changes are made to README.md**.
