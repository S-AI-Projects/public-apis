# R02-T040 — Manual Verification Decisions and Technical Rationale

## Overview

This document records the manual verification decisions, technical rationale,
official source references, and evidence analysis for the three assigned APIs
in the `### Patent` section of `public-apis`:

1. **EPO** (`https://developers.epo.org/`)
2. **PatentsView** (`https://patentsview.org/apis/purpose`)
3. **TIPO** (`https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00`)

---

## Decision 1: EPO (European Patent Office)

### 1. Official Documentation URLs
- Developer Portal: `https://developers.epo.org/`
- Service Documentation: `https://developers.epo.org/ops-v3-2/documentation`
- OAuth Token Endpoint: `https://ops.epo.org/3.2/auth/accesstoken`

### 2. Observed Technical Facts
- **Service Name**: Open Patent Services (OPS) v3.2.
- **Authentication**:
  - Developers register an account on the EPO Developer Portal.
  - Creating an application generates a Consumer Key and Consumer Secret.
  - The client exchanges credentials via OAuth 2.0 Client Credentials Grant (`POST https://ops.epo.org/3.2/auth/accesstoken`).
  - Subsequent requests pass the token in the header: `Authorization: Bearer <access_token>`.
  - In `CONTRIBUTING.md`, this mechanism is classified as `OAuth`.
- **Protocol**: Exclusively served over HTTPS (`https://ops.epo.org/...`).
- **CORS Support**: Cross-Origin Resource Sharing headers are undocumented in official developer guides. Per policy, CORS is not inferred from the web portal.

### 3. Historical Information
- OPS has consistently utilized OAuth 2.0 client credential authentication across v2.x and v3.x architectures.

### 4. Unverified Information
- CORS headers for third-party browser execution remain unverified in official documentation.

### 5. Manual Decision & Rationale
- **Action**: Retain existing catalogue entry as-is.
- **Before Metadata**: `Auth: OAuth`, `HTTPS: Yes`, `CORS: Unknown`
- **Recommended After**: `Auth: OAuth`, `HTTPS: Yes`, `CORS: Unknown`
- **Rationale**: The existing catalogue entry accurately reflects the verified OAuth 2.0 authentication requirement and HTTPS protocol.

---

## Decision 2: PatentsView

### 1. Official Documentation URLs
- Legacy Documentation URL (Assigned): `https://patentsview.org/apis/purpose`
- Legacy Endpoint Documentation: `https://patentsview.org/apis/api-endpoints`
- Legacy Query Endpoint: `https://api.patentsview.org/patents/query`
- Current PatentSearch Portal: `https://search.patentsview.org/`
- Current PatentSearch Documentation: `https://search.patentsview.org/docs/`
- USPTO Open Data Portal: `https://data.uspto.gov/`
- USPTO API Directory: `https://api.uspto.gov/`

### 2. Observed Technical Facts
- **Legacy API Authentication**:
  - The legacy API endpoints documented under `https://patentsview.org/apis/purpose` were completely open and unauthenticated.
  - Official legacy documentation states: "The PatentsView API is a free, publicly accessible RESTful interface for querying patent data. No API key is required to access the API endpoints."
  - Under `CONTRIBUTING.md`, open access APIs that do not require credentials are classified as `No`.
- **Current PatentSearch API Authentication**:
  - The newer PatentSearch API at `https://search.patentsview.org/docs/` requires account registration.
  - Authenticated queries must supply the registered API key via the `X-Api-Key` HTTP header.
  - Under `CONTRIBUTING.md`, this is classified as `apiKey`.
- **USPTO Open Data Portal Migration**:
  - The USPTO announced the consolidation of patent data services under the USPTO Open Data Portal (`data.uspto.gov` / `api.uspto.gov`).
  - PatentsView documentation alerts users to this ongoing migration and the transition of legacy endpoints.

### 3. Historical Information
- From its launch through 2024, PatentsView provided open patent research data without requiring registration or keys. The introduction of the PatentSearch API and the USPTO ODP represents a multi-stage transition.

### 4. Unverified Information
- The exact decommission schedule for legacy endpoints versus the completion date of the USPTO ODP migration is not published in a single static deadline.

### 5. Manual Decision & Rationale
- **Action**: Keep root `README.md` unchanged (`Auth: No`, `HTTPS: Yes`, `CORS: Unknown`).
- **Rationale**:
  - The assigned URL is `https://patentsview.org/apis/purpose`, which specifically documents the legacy API purpose and unauthenticated endpoints.
  - Per Section 5 of the task instructions: "Do not apply new API authentication requirements to a legacy API without explaining the version distinction."
  - Per Section 6: "If a correction is recommended but not sufficiently established, leave README unchanged and report the recommendation separately."
  - Changing the catalogue Auth field to `apiKey` for the legacy `/apis/purpose` URL would incorrectly assert that the legacy endpoint required an API key.
  - The version distinction between the legacy open API (`No`) and the current PatentSearch API (`apiKey`) is documented transparently in this report and in `evidence.md`.

---

## Decision 3: TIPO (Taiwan Intellectual Property Office)

### 1. Official Documentation URLs
- Assigned Service Portal: `https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD05.aspx?QryDS=API00`
- Open Data Platform Overview: `https://tiponet.tipo.gov.tw/Gazette/OpenData/`
- Member Registration & Guidelines: `https://tiponet.tipo.gov.tw/Gazette/OpenData/OD/OD01.aspx`
- Taiwan Government Open Data Portal Entry: `https://data.gov.tw/dataset/33314`

### 2. Observed Technical Facts
- **Assigned Dataset**:
  - Service Code: `API00` (專利公報開放資料 / Patent Gazette Open Data).
  - Agency: Taiwan Intellectual Property Office, Ministry of Economic Affairs (經濟部智慧財產局).
- **Authentication & Credential Flow**:
  - Step 1 (Registration): Developers register a member account on the TIPONet Gazette Open Data platform (`https://tiponet.tipo.gov.tw/`).
  - Step 2 (Token Issuance): Developers authenticate with their registered account and password (using HTTP Basic authentication or the account verification API) to request an access token. TIPO issues an access token string.
  - Step 3 (Bearer Token Usage): To query or retrieve patent gazette datasets (such as `API00`), client requests must supply the token in the HTTP `Authorization` header as `Bearer <token>` (or pass the token parameter in the request query).
- **Classification under CONTRIBUTING.md**:
  - In `CONTRIBUTING.md`, the five accepted values for `Auth` are: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`.
  - `CONTRIBUTING.md` explicitly specifies:
    `` `apiKey` - the API uses a private key string/token for authentication - try and use the correct parameter ``.
  - TIPO does not implement an OAuth 2.0 authorization server (no redirect URIs, OAuth scopes, authorization codes, or third-party consent screens). It issues a private user token.
  - Under `CONTRIBUTING.md` rules, private token authentication is properly classified as `apiKey`.
- **Protocol & CORS**:
  - The API operates over HTTPS (`Yes`).
  - Cross-Origin Resource Sharing is not documented for browser clients; classified as `Unknown`.

### 3. Historical Information
- TIPO launched programmatic Gazette Open Data APIs under the Taiwan Executive Yuan Open Data directive, transitioning legacy subscriber CD/DVD distribution to token-authenticated REST downloads.

### 4. Unverified Information
- CORS headers for third-party browser domains and machine-readable OpenAPI specifications for dataset `API00` remain unverified externally on `tiponet.tipo.gov.tw`.

### 5. Manual Decision & Rationale
- **Action**: Retain existing catalogue entry as-is.
- **Before Metadata**: `Auth: apiKey`, `HTTPS: Yes`, `CORS: Unknown`
- **Recommended After**: `Auth: apiKey`, `HTTPS: Yes`, `CORS: Unknown`
- **Rationale**: `apiKey` is the exact, appropriate classification for private token authentication under the definitions in `CONTRIBUTING.md`.

---

## Decision 4: Root README Modification Policy

### Policy & Evaluation
- All three assigned catalogue entries (`EPO`, `PatentsView`, `TIPO`) conform to `CONTRIBUTING.md` syntax, cell padding, column counts, and permitted enum values.
- All entries reflect verified technical classifications when accounting for version distinctions.
- Per Section 6: "Only modify the root README if the evidence conclusively proves that a correction is needed. The checker and its report are the required contribution even if the existing entries are already correct. If a correction is recommended but not sufficiently established, leave README unchanged and report the recommendation separately."
- Therefore, the root `README.md` is left unchanged.
