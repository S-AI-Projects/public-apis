# R02-T035 — Evidence Table

Verified on 2026-11-17. Scoped to the README `### News` table (lines 1851–1879).

| API | Field | Current value | Observed value | Proposed value | Source URL | Reasoning |
|:---|:---|:---|:---|:---|:---|:---|
| Mediastack | Auth | `apiKey` | `apiKey` via `access_key` query parameter | `apiKey` | https://docs.apilayer.com/mediastack/docs/quickstart-guide | Official quickstart shows `https://api.mediastack.com/v1/news?access_key=YOUR_ACCESS_KEY`; no change. |
| Mediastack | HTTPS | Yes | Yes | Yes | https://docs.apilayer.com/mediastack/docs/api-documentation | Official documentation states the REST service supports HTTPS encryption and uses an HTTPS endpoint; no change. |
| Mediastack | CORS | Unknown | Yes | Yes | https://api.mediastack.com/v1/news | A documented `GET` request with `Origin: https://example.com` returned `access-control-allow-origin: *`; the 401 was only due to a missing key, so the CORS header is conclusive. |
| Associated Press | Auth | `apiKey` | `apiKey` via `x-api-key` header | `apiKey` | https://api.ap.org/media/v/docs/Getting_Started_API.htm | Official docs require an API key in the `x-api-key` (or legacy `x-apikey`) request header; no change. |
| Associated Press | HTTPS | Yes | Yes, TLS 1.2/1.3 | Yes | https://api.ap.org/media/v/docs/Getting_Started_API.htm | Official docs require HTTPS with TLS 1.2 or 1.3 for all requests to `api.ap.org`; no change. |
| Associated Press | CORS | Unknown | Inconclusive | Unknown | https://api.ap.org/media/v/docs/Getting_Started_API.htm | `OPTIONS` returned a gateway-level `Access-Control-Allow-Origin` echo, but the unauthenticated `GET` did not return that header, and official docs explicitly say there are no supported browser-based integrations. No conclusive official CORS guarantee, so retain `Unknown`. |
| Chronicling America | Auth | No | No | No | https://guides.loc.gov/chronicling-america/additional-features | Official LOC guide states the API is accessible with no API key or authentication required; no change. |
| Chronicling America | HTTPS | No | Yes | Yes | https://www.loc.gov/apis/additional-apis/chronicling-america-api/ | LOC states that from 2025 the collection is accessible exclusively via the loc.gov API; the official API page and JSON endpoint are HTTPS, and the legacy HTTP URL returns a 308 redirect to HTTPS. |
| Chronicling America | CORS | Unknown | Inconclusive | Unknown | https://www.loc.gov/collections/chronicling-america/?fo=json | The actual collection endpoint returned HTTP 403 without an `access-control-allow-origin` header. That is an inconclusive challenge response, not proof that CORS is unsupported, so retain `Unknown`. |

## README changes

These README corrections are applied:

- Line 1854, Mediastack: `CORS` changed from `Unknown` to `Yes`.
- Line 1856, Chronicling America: documentation URL updated to the current HTTPS LOC API page.
- Line 1856, Chronicling America: `HTTPS` changed from `No` to `Yes`.

The Associated Press row and all other entries are unchanged.
