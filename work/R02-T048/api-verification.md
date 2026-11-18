# API Verification — R02-T048 (Authentication & Authorization)

Assigned entries: lines 306–308 of README.md (commit 2676ca49)

| # | API Name | URL | HTTP Status | Auth | HTTPS | CORS | Notes |
|---|----------|-----|-------------|------|-------|------|-------|
| 1 | Auth0 | https://auth0.com | 200 OK | `apiKey` | Yes | Yes | Live — primary auth/authz platform; free tier + paid plans; API key required for SDK integration |
| 2 | GetOTP | https://otp.dev/en/docs/ | 200 OK | `apiKey` | Yes | No | Live — OTP-as-a-service; registration and API key needed; CORS not supported (server-to-server use) |
| 3 | MojoAuth | https://mojoauth.com | 200 OK | `apiKey` | Yes | Yes | Live — passwordless auth service; free tier available; API key required |

## Access Requirement Summary

### Auth0
- **Requires**: Registration + API key (Client ID/Secret)
- **Free tier**: Yes (up to 7,500 MAU free)
- **HTTPS**: Enforced — all endpoints served over TLS
- **CORS**: Yes — supports browser-side SDK calls
- **Catalogue fields**: `apiKey | Yes | Yes` ✅ — correct, no change needed

### GetOTP
- **Requires**: Registration + API key
- **Free tier**: Yes (limited quota)
- **HTTPS**: Enforced
- **CORS**: No — designed for server-side integration, not browser fetch
- **Catalogue fields**: `apiKey | Yes | No` ✅ — correct, no change needed

### MojoAuth
- **Requires**: Registration + API key
- **Free tier**: Yes
- **HTTPS**: Enforced
- **CORS**: Yes — supports browser-based passwordless flows
- **Catalogue fields**: `apiKey | Yes | Yes` ✅ — correct, no change needed

## Conclusion

All three assigned entries have accurate Auth/HTTPS/CORS metadata. No README.md changes required.
No credentials were saved during this verification. Any API key obtained would be used only for
integration testing (outside scope of this task).
