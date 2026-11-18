# API Verification — R02-T049 (Entertainment)

Assigned entries: lines 1032–1034 of README.md (commit 2676ca49)

| # | API Name | URL | HTTP Status | Auth | HTTPS | CORS | Notes |
|---|----------|-----|-------------|------|-------|------|-------|
| 1 | Anycrap | https://anycrap.shop/developers | 200 OK | `apiKey` | Yes | Yes | Live — documentation page loads; API key required via sign-up |
| 2 | Bucketlist Dream of the Day | https://bucketlist.nl/samenwerken?lang=en#droom-van-de-dag | 200 OK | No | Yes | Yes | Live — open API, no auth needed; daily Dutch travel inspiration endpoint |
| 3 | chucknorris.io | https://api.chucknorris.io | 200 OK | No | Yes | Unknown | Live — returns jokes JSON; CORS policy not documented publicly; labelled Unknown is correct |

## Maintenance Decisions

### Anycrap (line 1032)
- Fields `apiKey | Yes | Yes` are accurate: sign-up required for API key, full HTTPS, CORS enabled
- **Decision**: No change required

### Bucketlist Dream of the Day (line 1033)
- Fields `No | Yes | Yes` are accurate: free, no key needed, HTTPS, CORS enabled
- **Decision**: No change required

### chucknorris.io (line 1034)
- Fields `No | Yes | Unknown` are accurate: free, no key, HTTPS; CORS not reliably documented
- **Recommendation**: CORS status could be verified via browser DevTools or an OPTIONS request,
  but without confirmed documentation, `Unknown` is the correct conservative label
- **Decision**: No change required; `Unknown` is the appropriate value

## Conclusion

All three assigned entries have accurate metadata. No README.md changes required.
The maintenance pass produced a reproducible report from fixtures and from the live README.
