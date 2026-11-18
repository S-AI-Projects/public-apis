# R02-T040 — Patent Section Evidence and Technical Analysis

## Task summary

Implement a standard-library-only Python checker for the `### Patent` section
of `public-apis` README, validating the table structure, contribution rules,
and three selected API entries:

1. **EPO** — `https://developers.epo.org/`
2. **PatentsView** — `https://patentsview.org/apis/purpose`
3. **TIPO** — `https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00`

Pinned baseline commit: `2676ca49d557ef14a0f478311506dae947639028`

---

## Selected Entries: Before vs. Recommended After

| API | Dynamic Line | Before Auth | Before HTTPS | Before CORS | Recommended Auth | Recommended HTTPS | Recommended CORS |
|-----|:------------:|:-----------:|:------------:|:-----------:|:----------------:|:-----------------:|:----------------:|
| EPO | 1994 | `OAuth` | Yes | Unknown | `OAuth` | Yes | Unknown |
| PatentsView | 1995 | No | Yes | Unknown | No* | Yes | Unknown |
| TIPO | 1996 | `apiKey` | Yes | Unknown | `apiKey` | Yes | Unknown |

\* Recommendation note: Legacy PatentsView API endpoint at `https://patentsview.org/apis/purpose` was unauthenticated (`No`). The newer PatentSearch API requires `apiKey` (`X-Api-Key`), with migration planned to the USPTO Open Data Portal (`data.uspto.gov`). Per policy, `README.md` is preserved without edits.

---

## Mandatory Contribution Rules Enforced

From `CONTRIBUTING.md`:

- **Auth** allowed values: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`
- **CORS** allowed values: `Yes`, `No`, `Unknown`
- **HTTPS** allowed values: `Yes`, `No`
- **Ordering**: alphabetical per section (case-insensitive)
- **Description**: must not exceed 100 characters
- **Column padding**: each column padded with exactly one space on either side (rejects both missing spaces and multiple spaces)
- **Header format**: `API | Description | Auth | HTTPS | CORS |`
- **Separator format**: `|:---|:---|:---|:---|:---|`

---

## Technical Investigation & Manual Verification

### 1. EPO (European Patent Office)
- **Official Documentation URLs**:
  - Portal: `https://developers.epo.org/`
  - OPS Documentation: `https://developers.epo.org/ops-v3-2/documentation`
  - OAuth Token Endpoint: `https://ops.epo.org/3.2/auth/accesstoken`
- **Observed Technical Facts**:
  - Service: Open Patent Services (OPS) v3.2.
  - Authentication: User registration produces Consumer Key and Secret. Access tokens are requested via OAuth 2.0 Client Credentials flow (`POST https://ops.epo.org/3.2/auth/accesstoken`). Requests supply `Authorization: Bearer <access_token>`.
  - Protocol: Exclusively HTTPS.
  - CORS: Cross-Origin Resource Sharing is undocumented for third-party browser clients. CORS is not inferred from the web portal.
- **Historical Information**:
  - OPS has consistently utilized OAuth 2.0 across v2.x and v3.x releases.
- **Unverified Information**:
  - Direct browser cross-origin execution headers remain unverified without live header capture.
- **Manual Decision & Recommendation**:
  - Catalogue entry line 1994 lists `OAuth`, `Yes`, `Unknown`. Retain as-is.

### 2. PatentsView
- **Official Documentation URLs**:
  - Legacy Purpose (Assigned): `https://patentsview.org/apis/purpose`
  - Legacy Endpoints: `https://patentsview.org/apis/api-endpoints`
  - Legacy Endpoint: `https://api.patentsview.org/patents/query`
  - Current PatentSearch Docs: `https://search.patentsview.org/docs/`
  - USPTO Open Data Portal: `https://data.uspto.gov/`
  - USPTO API Directory: `https://api.uspto.gov/`
- **Observed Technical Facts**:
  - **Version Distinction**:
    - **Legacy PatentsView API**: Documented at `/apis/purpose` as open, free, unauthenticated REST access (`Auth: No`).
    - **Current PatentSearch API**: Requires registration to obtain an API key, passed via the `X-Api-Key` HTTP header (`Auth: apiKey`).
    - **USPTO Open Data Portal**: USPTO announced the transition of patent data services to the Open Data Portal (`data.uspto.gov` / `api.uspto.gov`).
  - **Formatting**: Name cell in README contains a minor trailing space `[PatentsView ]`. The row is otherwise structurally valid.
- **Historical Information**:
  - PatentsView operated from inception through 2024 as an open, unauthenticated service.
- **Unverified Information**:
  - Exact decommissioning timeline for legacy endpoints vs. full transition to USPTO ODP remains in progress.
- **Manual Decision & Recommendation**:
  - The assigned URL refers specifically to legacy API documentation. Applying `apiKey` to this legacy URL without version distinction is prohibited.
  - Per Section 6: "If a correction is recommended but not sufficiently established, leave README unchanged and report the recommendation separately."
  - README line 1995 is retained as-is (`No`, `Yes`, `Unknown`).

### 3. TIPO (Taiwan Intellectual Property Office)
- **Official Documentation URLs**:
  - Assigned Portal: `https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00`
  - Platform Overview: `https://tiponet.tipo.gov.tw/Gazette/OpenData/`
  - Member Registration: `https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD01.aspx`
  - Taiwan Open Data Portal: `https://data.gov.tw/dataset/33314`
- **Observed Technical Facts**:
  - Service: Taiwan Intellectual Property Office Gazette Open Data service (`API00`: 專利公報開放資料).
  - Authentication: Users register a member account on TIPONet, authenticate with account/password to receive an access token, and supply the token as a Bearer token in the `Authorization` header (`Bearer <token>`).
  - Classification: In `CONTRIBUTING.md`, `apiKey` is defined as: "the API uses a private key string/token for authentication - try and use the correct parameter".
  - TIPO does not implement an OAuth 2.0 authorization server; private token authentication is properly classified as `apiKey`.
  - Protocol: HTTPS is supported.
  - CORS: Undocumented for browser clients; classified as `Unknown`.
- **Historical Information**:
  - TIPO launched programmatic Gazette Open Data under the Executive Yuan Open Data initiative, transitioning from batch distribution to token-authenticated REST downloads.
- **Unverified Information**:
  - CORS headers for third-party browser clients and machine-readable OpenAPI specs for dataset `API00` remain unverified externally on `tiponet.tipo.gov.tw`.
- **Manual Decision & Recommendation**:
  - Retain line 1996 as `apiKey`, `Yes`, `Unknown`.

---

## Ordering and Neighbor Relationships

The `### Patent` section starts at line 1991:
- Line 1992: Table header
- Line 1993: Table separator
- Line 1994: `EPO` (casefold: `"epo"`)
- Line 1995: `PatentsView` (casefold: `"patentsview"`)
- Line 1996: `TIPO` (casefold: `"tipo"`)
- Line 1997: `USPTO` (casefold: `"uspto"`)

Neighbor verification:
- Preceding neighbor of `EPO`: None (first row in section).
- Following neighbor of `EPO`: `PatentsView`.
- Preceding neighbor of `PatentsView`: `EPO`.
- Following neighbor of `PatentsView`: `TIPO`.
- Preceding neighbor of `TIPO`: `PatentsView`.
- Following neighbor of `TIPO`: `USPTO`.

Alphabetical comparison:
`"epo"` < `"patentsview"` < `"tipo"` < `"uspto"`

The sequence is strictly alphabetical and case-insensitive.

---

## Unverified External Evidence Policy

- Unverified external documentation or inconclusive automated reachability probes are retained as inconclusive observations and do NOT become confirmed catalogue metadata errors.
- Automated reachability failure in an isolated or sandboxed environment does not imply an invalid catalogue entry.
- Tested offline in fixture `unverified-info.md` (passes with exit code 0).

---

## Root README Modification Policy

- All three existing catalogue rows conform to `CONTRIBUTING.md` syntax and allowed values.
- Observed documentation facts confirm that existing catalogue metadata accurately reflects the assigned APIs (with version nuances for PatentsView thoroughly documented).
- No edit to root `README.md` is warranted. Root `README.md` remains clean and unchanged.
