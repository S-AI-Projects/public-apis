# Coursework Checks — R02-T029: Verify Access Requirements (Documents & Productivity)

This directory contains deterministic offline verification checkers, access evidence rules, and test fixtures for coursework task R02-T029.

---

## 1. Task Purpose & Selected Entries

The purpose of this check is to verify whether selected resources in the **Documents & Productivity** category require authentication, registration, payment, or a specific environment, and to make their catalogue descriptions and metadata precise.

Assigned Entries:

| API Name | Source Line | URL | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|:---|
| **AgentPay Doc Tools** | Line 923 | `https://agentpay-tools.agentpay-apis.workers.dev` | No | Yes | Yes |
| **Airtable** | Line 924 | `https://airtable.com/api` | `OAuth` | Yes | Yes |
| **Api2Convert** | Line 925 | `https://www.api2convert.com/` | `apiKey` | Yes | No |

Category Section Header: `### Documents & Productivity` (Line 920 in root `README.md`)

---

## 2. Verified Access Requirements & Evidence

### 1. AgentPay Doc Tools
- **Authentication:** `No` (for conventional identity/account authentication). The catalogue `Auth` field is `No` under repository contribution rules because user account registration, user login, API keys, and pre-shared identity credentials are not required.
- **Payment Authorization:** Explicitly distinguished from authentication. While conventional authentication is `No`, **cryptographic payment authorization is strictly required for paid API calls** via the x402 `PAYMENT-SIGNATURE` header (or prepaid credit token via `Authorization: Bearer <key>`). Invocations without payment authorization return `HTTP 402 Payment Required`.
- **Registration:** `No`. Anonymous access supported; no account signup or email required.
- **Payment:** `Yes`. Pay-per-request via x402 in USDC on Base or Algorand ($0.005–$0.01 per request).
- **Free Tier / Trial:** `Yes`. `GET /credits/trial` provides an API key with $0.05 trial credit (one per network per day).
- **Environment:** `No`. Open HTTP API with no specific environment, workspace, or account tier required.
- **Public vs. API Distinction:** Public landing page is readable without credentials or payment; API tool endpoints return `HTTP 402 Payment Required` unless payment authorization headers or credit keys are sent.
- **Evidence URLs:**
  - `https://agentpay-tools.agentpay-apis.workers.dev`
  - `https://agentpay-tools.agentpay-apis.workers.dev/tools/openapi.json`
  - `https://agentpay-tools.agentpay-apis.workers.dev/tools/llms.txt`

### 2. Airtable
- **Authentication:** `Yes`. All API requests require HTTP Bearer tokens. API keys were formally deprecated on February 1, 2024. Supported methods are `OAuth` and Personal Access Tokens (PATs).
- **Registration:** `Yes`. Requires an active Airtable user account.
- **Payment:** `No`. Free plan available indefinitely (unlimited bases, up to 1,000 records per base, 1GB attachments).
- **Free Tier / Trial:** `Yes`. Perpetual free plan.
- **Environment:** `Yes`. Access tokens are strictly scoped to specific workspaces, bases, and permission scopes.
- **Public vs. API Distinction:** Documentation is publicly readable; API data endpoints return `HTTP 401 Unauthorized` without valid authentication.
- **Evidence URLs:**
  - `https://airtable.com/developers/web/api/authentication.md`
  - `https://airtable.com/developers/web/api/introduction.md`
  - `https://support.airtable.com/docs/airtable-api-key-deprecation-notice`
  - `https://airtable.com/pricing`

### 3. Api2Convert
- **Authentication:** `Yes`. API key required via `x-api2convert-api-key` header (or single-job token via `x-api2convert-token`).
- **Registration:** `Yes`. Account registration required to obtain API key from dashboard.
- **Payment:** `No`. Free tier available; packages and recurring monthly subscriptions available for high-volume conversion.
- **Free Tier / Trial:** `Yes`. 30 free credits renewed every 24 hours for every registered user.
- **Environment:** `No`. Standard cloud REST API with no local deployment or workspace binding.
- **Public vs. API Distinction:** Read-only informational endpoints (`GET /v2/conversions`, `GET /v2/presets`) are public; file conversion operations require authentication and credit deduction.
- **Evidence URLs:**
  - `https://www.api2convert.com/documentation/guides/authentication`
  - `https://www.api2convert.com/documentation/guides/quickstart`
  - `https://www.api2convert.com/pricing`

---

## 3. Discrepancies, Catalogue Corrections & Failure Behavior

1. **Airtable:**
   - `Auth`: Updated from `` `apiKey` `` to `` `OAuth` ``. Airtable completely deprecated API keys on February 1, 2024; OAuth 2.0 is the official standard.
   - `CORS`: Updated from `Unknown` to `Yes`. Live OPTIONS preflight to `https://api.airtable.com/v0/...` returns `access-control-allow-origin: *`.
2. **Api2Convert:**
   - `CORS`: Updated from `Unknown` to `No`. API does not return `Access-Control-Allow-Origin` headers on preflight or GET requests; cross-origin browser calls are not permitted.
3. **AgentPay Doc Tools:**
   - Preserved `Auth: No`, `HTTPS: Yes`, `CORS: Yes`. Matches repo conventions for x402 pay-per-call services and verified headers.

### Discrepancy Failure Enforcement
The normal checker treats any catalogue discrepancies as a failing condition: `python3 tools/course_checks/r02-t029.py` exits with non-zero exit code (`sys.exit(1)`) whenever `discrepancies_detected > 0`, in addition to schema errors, missing entries, duplicate entries, or formatting issues.

---

## 4. Offline Fixture Coverage

Fixtures are located under `tools/course_checks/fixtures/r02-t029/`:

1. `valid_entries.md`: Positive baseline of valid table syntax and accurate metadata for Documents & Productivity.
2. `missing_required_field.md`: Row with an empty Description field, detected and reported as a format issue.
3. `malformed_row.md`: Row containing 3 columns instead of 5, rejected with line number and column counts.
4. `source_line_tracking.md`: Tests line tracking accuracy with preambles and empty line offsets.
5. `auth_required.json`: Fixture validating authentication requirements (OAuth/apiKey vs. x402 payment authorization).
6. `registration_required.json`: Fixture validating registration requirements (anonymous access vs. registered accounts).
7. `paid_access_free_tier.json`: Fixture validating pay-per-call vs. free tiers, ensuring free tiers are not conflated with unrestricted free usage.
8. `environment_specific.json`: Fixture validating workspace/base scoping requirements.
9. `conflicting_inconclusive.json`: Evaluates resource with conflicting provider terms, correctly classified as `unverified`.
10. `unavailable_unverified.json`: Evaluates resource unreachable via timeout/error, correctly classified as `unverified` without assuming discontinued or broken.
11. `evidence_url_preservation.json`: Validates that every verified access claim preserves an authoritative `https://` documentation URL.
12. `duplicate_entries.md`: Detects duplicate entries appearing within the target category.
13. `unicode_and_markdown_urls.md`: Verifies preservation of Unicode characters and complex URLs with queries/parentheses.
14. `outside_category.md`: Verifies that entries under other categories (`Animals`, `Dictionaries`) are ignored.
15. `incorrect_metadata.md`: Verifies discrepancy detection, recommended edit generation for outdated metadata, and regression tests that discrepancies cause a failing validation condition.
16. `CLI --intentional-failure`: Verified via an isolated subprocess test ensuring the `--intentional-failure` flag exits non-zero without terminating the self-test runner.

---

## 5. Usage & Verification Commands

### Run Deterministic Offline Self-Tests
```bash
python3 tools/course_checks/r02-t029.py --self-test
```

### Run Normal Checker Against Root README.md
```bash
python3 tools/course_checks/r02-t029.py
```

### Python Bytecode Compilation Check
```bash
python3 -m py_compile tools/course_checks/r02-t029.py
```

### Git Whitespace & Format Check
```bash
git diff --check
```
