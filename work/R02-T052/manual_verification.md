# Manual Verification of Selected Entries (R02-T052)

**Observation Date**: 2026-11-22  
**Observer**: `divyanshiyadav396-lab` (via browser agent)  
**Target Section**: `### Anti-Malware` in `README.md` (Lines 241-260)  

## Verification Table

| Entry | README Line | URL in README | Official Docs URL Observed | Auth Verified | HTTPS Verified | CORS Verified | Observation Date | Notes |
|:---|:---|:---|:---|:---|:---|:---|:---|:---|
| **AbuseIPDB** | 244 | `https://docs.abuseipdb.com/` | `https://docs.abuseipdb.com/#introduction` | `apiKey` | Yes | NOT OBSERVED | 2026-11-22 | Page loaded (`Introduction – AbuseIPDB APIv2 Documentation`). Documentation states auth via `Key: <YOUR_API_KEY>` header or `?key=`. Stated endpoint URLs use HTTPS. Response headers for live API endpoints could not be directly observed; CORS is marked `Unknown` in README.md. No duplicate URLs found. |
| **AlienVault Open Threat Exchange (OTX)** | 245 | `https://otx.alienvault.com/api` | `https://otx.alienvault.com/api` | `apiKey` | Yes | NOT OBSERVED | 2026-11-22 | Page loaded (`OTX DirectConnect API - LevelBlue - Open Threat Exchange`). Documentation states auth via `X-OTX-API-KEY: <INSERT_USER_API_KEY>` header. Stated endpoint URLs use HTTPS. Live API response headers could not be directly observed in the environment; CORS is marked `Unknown` in README.md. No duplicate URLs found. |
| **CAPEsandbox** | 246 | `https://capev2.readthedocs.io/en/latest/usage/api.html` | `https://capev2.readthedocs.io/en/latest/usage/api.html` | `apiKey` | Yes | NOT OBSERVED | 2026-11-22 | Page loaded (`REST API — CAPE Sandbox v2.5 Book`). Documentation states Token auth (`Authorization: Token <token>`). Documentation hosted over HTTPS. CORS behavior is not documented in the Sphinx docs and live headers were not observed; CORS is marked `Unknown` in README.md. Public demo server `capesandbox.com` returned Cloudflare Error 523. No duplicate URLs found. |

## Host-Verified Browser Facts
- **Visited Origins**: `https://docs.abuseipdb.com`, `https://otx.alienvault.com`, `https://capev2.readthedocs.io`, `https://capesandbox.com`
- **Blocked / Unreachable Origins**: `https://capesandbox.com` (Cloudflare Error 523: origin unreachable on public demo server)
- **Latest Screenshot**: `/Users/divyanshiyadav/.gemini/antigravity/brain/daf1250f-5fd7-4b56-b47c-af2fa2d639fe/browser_evidence/f502e499-ce8f-483f-8f4b-30619053724f/final_step_43.png`

## What Was NOT OBSERVED & Manual Verification Steps
- **CORS Headers**: Live HTTP response headers (specifically `Access-Control-Allow-Origin`) for API requests could not be observed directly from the sandboxed environment. Therefore, CORS is marked **NOT OBSERVED**, and `Unknown` in `README.md` is strictly preserved as the safe and accurate unverified designation.
- **Manual Verification Steps for Reviewer**:
  1. **AbuseIPDB**: On a host machine with network and API key, run `curl -sI -H "Key: <YOUR_KEY>" https://api.abuseipdb.com/api/v2/check?ipAddress=8.8.8.8` to inspect response headers for `Access-Control-Allow-Origin`.
  2. **AlienVault OTX**: Run `curl -sI -H "X-OTX-API-KEY: <YOUR_KEY>" https://otx.alienvault.com/api/v1/indicators/IPv4/8.8.8.8/general` to inspect response headers for `Access-Control-Allow-Origin`.
  3. **CAPEsandbox**: Access a running CAPE instance's `/apiv2/` endpoint from a web browser JavaScript `fetch()` call originating on another domain to test if cross-origin requests succeed or are blocked. Note that the public demo at `https://capesandbox.com` is currently unreachable (Cloudflare Error 523).

## README.md Decision
- **Decision**: **No change**.
- **Reasoning**: All three documentation URLs in `README.md` are accurate, active, and resolve to the official documentation. Auth is `apiKey` for all three as observed in their documentation. HTTPS is supported. Because CORS response headers were NOT OBSERVED, `Unknown` is retained. No duplicate URLs exist. Therefore, `README.md` is left untouched.
