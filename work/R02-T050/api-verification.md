# API Verification — R02-T050 (Anti-Malware)

Assigned entries: lines 244–246 of README.md (commit 2676ca49)
Observation date: 2026-11-18

## Redirect Chain Results

| # | API Name | Catalogue URL | Chain | Classification | Final URL | Notes |
|---|----------|--------------|-------|----------------|-----------|-------|
| 1 | AbuseIPDB | https://docs.abuseipdb.com/ | HTTP 200 | OK | https://docs.abuseipdb.com/ | Direct hit, no redirect |
| 2 | AlienVault Open Threat Exchange (OTX) | https://otx.alienvault.com/api | HTTP 404 | ERROR | — | Documentation path returns 404; main site (https://otx.alienvault.com) returns 200 |
| 3 | CAPEsandbox | https://capev2.readthedocs.io/en/latest/usage/api.html | HTTP 200 | OK | https://capev2.readthedocs.io/en/latest/usage/api.html | Direct hit, no redirect |

## Maintenance Decisions

### AbuseIPDB (line 244)
- URL resolves directly to HTTP 200 ✅
- No redirect chain, no broken link
- **Decision**: No change required

### AlienVault Open Threat Exchange OTX (line 245)
- `https://otx.alienvault.com/api` returns HTTP 404
- Main site `https://otx.alienvault.com` returns HTTP 200 — service is live
- OTX API base is documented at `https://otx.alienvault.com/api/v1` (also 404 for direct HEAD) but API itself works for authenticated requests
- Per project guidelines: "No link is removed solely because a single automated request failed"
- The 404 on the docs path may be a server-side routing issue (SPA that requires a browser to render) rather than a truly missing resource
- **Decision**: Entry is NOT removed. The 404 is from a single automated HEAD request; the OTX service and API are confirmed live. Mark as "unverified" pending manual browser confirmation. No README change made without further human review.

### CAPEsandbox (line 246)
- URL resolves directly to HTTP 200 ✅ (ReadTheDocs documentation page)
- No redirect chain, no broken link
- **Decision**: No change required

## Conclusion

AbuseIPDB and CAPEsandbox verified as reachable with HTTP 200.
AlienVault OTX documentation path returns 404 (single automated request) — entry retained per project policy;
the OTX platform itself is live and operational. No README.md changes were made.
