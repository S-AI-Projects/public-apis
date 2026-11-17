# R02-T036 evidence

Verification date: 2026-11-17.

Category and table: `Vehicle`, README heading `### Vehicle` (line 2651), table
lines 2651-2671. Selected entries are at README lines 2654-2656.

## Evidence table

| API | Field | Current value | Observed value | Proposed value | Source URL | Reasoning |
| --- | --- | --- | --- | --- | --- | --- |
| Auto Body Shop Directory | Auth | No | No authentication required by the documented public endpoints; the OpenAPI 3.0.2 document has no `security` section or security schemes. | No | https://autobodyshopnear.com/developers/body-shop-api | Documentation describes five public `GET` endpoints and a keyless quickstart. Existing value is correct. |
| Auto Body Shop Directory | HTTPS | Yes | OpenAPI server URL is `https://autobodyshopnear.com/api/v1/public`; documentation is served over HTTPS. | Yes | https://autobodyshopnear.com/developers/body-shop-api/openapi.json | HTTPS is explicitly documented. Existing value is correct. |
| Auto Body Shop Directory | CORS | No | Official documentation does not state a CORS policy. Direct requests to the documentation and API paths received HTTP 403 Cloudflare challenges with no `Access-Control-Allow-Origin` header. Third-party listings disagree (some say No, one says Yes). | No | https://autobodyshopnear.com/developers/body-shop-api | Evidence is inconclusive. A Cloudflare challenge is not evidence that the API is down, and no official CORS statement supports a change. Leave as-is. |
| Bike Reliability | Auth | No | Documentation says keyless calls are allowed up to 50 requests/day per IP; an optional free `X-Api-Key` raises the limit. A live keyless request returned HTTP 200. | No | https://bikereliability.co.uk/developers | Authentication is not required for the basic public API. Existing value is correct. |
| Bike Reliability | HTTPS | Yes | Documentation gives base URL `https://bikereliability.co.uk/api/v1`; live response included `strict-transport-security`. | Yes | https://bikereliability.co.uk/developers | HTTPS is explicitly documented and observed. Existing value is correct. |
| Bike Reliability | CORS | Yes | Documentation says "CORS is open"; live response included `access-control-allow-origin: *`. | Yes | https://bikereliability.co.uk/developers | Documentation and a live header agree. Existing value is correct. |
| BoltPatternHQ | Auth | No | Official page describes an MCP server installed with `npx -y boltpatternhq-mcp`; the three documented MCP tools require no authentication. | No | https://boltpatternhq.com/mcp/ | No authentication is documented. Existing value is correct. |
| BoltPatternHQ | HTTPS | Yes | The official documentation and site are served over HTTPS. The documented MCP transport is `stdio` rather than an HTTP API. | Yes | https://boltpatternhq.com/mcp/ | No evidence contradicts the site-level HTTPS value. Leave as-is. |
| BoltPatternHQ | CORS | Yes | The `/mcp/` and `/data/` HTML pages returned `access-control-allow-origin: *`. No REST API CORS policy is documented, and the MCP server itself uses `stdio`. | Yes | https://boltpatternhq.com/mcp/ | The API-specific CORS meaning is not established, but there is also no clear evidence for changing the existing value. Note: the wildcard CORS header comes from static documentation pages and does not prove CORS support for the MCP/stdio API. Leave as-is. |

## Catalogue result

No `README.md` changes were made. The existing Auth/HTTPS/CORS values for the
three selected entries were retained.

## Note on BoltPatternHQ

BoltPatternHQ's official documentation describes an MCP server distributed
through `npx`, not a REST API. The contribution guide has a separate `MCP
Servers` table with `Transport` and `Install` columns. Relocating the entry
would be a category change outside the assigned `Vehicle` table and would
remove it from the table this task requires the checker to validate. No
relocation or metadata change was made. The observation is recorded here so a
future task can review the category separately.

## Evidence limits

- Auto Body Shop Directory's documentation and API paths returned HTTP 403
  Cloudflare challenges from this network. The official documentation content
  and OpenAPI document were read through a text-rendering reader
  (`https://r.jina.ai/`) rather than through a successful direct request.
  The 403 responses were not treated as proof that the API is unavailable.
- No attempt was made to solve the Cloudflare challenge or to use a proxy to
  forge a successful API response.
- No live request was made to a BoltPatternHQ MCP tool; the documented server
  runs locally over `stdio`.
