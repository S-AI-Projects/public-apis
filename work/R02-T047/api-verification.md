# API Verification — R02-T047 (Sports & Fitness)

Assigned entries: lines 2355–2357 of README.md (commit 2676ca49)

| # | API Name | URL | HTTP Status | Notes |
|---|----------|-----|-------------|-------|
| 1 | 5DollarFootball | https://5dollarfootballapi.com/ | 200 OK | Live — responds normally |
| 2 | AcesAPI | https://acesapi.com/docs | 200 OK | Live — responds normally |
| 3 | API-FOOTBALL | https://www.api-football.com/documentation-v3 | 403 (Cloudflare WAF) | Live site behind WAF — NOT a missing resource; confirmed by Cloudflare headers |

## Notes

- API-FOOTBALL returns HTTP 403 due to Cloudflare Bot Management (WAF), not because the resource is absent.
  Cloudflare's standard bot-blocking response is not grounds for removal per project guidelines
  ("Never remove catalogue entries based on single automated failures").
- All three entries retain correct formatting: pipe-delimited row, valid markdown link syntax,
  proper Auth/HTTPS/CORS field values.
- No README.md changes required for this task.
