# R02-T039 — Books Section Checker

## Task summary

Implement a standard-library-only Python checker for the `### Books` section
of `public-apis` README, validating the table structure, contribution rules,
and three selected API entries:

1. **A Bíblia Digital** — `https://www.abibliadigital.com.br/en`
2. **Amanah Sunnah** — `https://sunnah.amanahagent.cloud/developers`
3. **Bhagavad Gita** — `https://docs.bhagavadgitaapi.in`

Pinned baseline commit: `2676ca49d557ef14a0f478311506dae947639028`

## Selected entries

| API | URL | Expected Historical Auth | HTTPS | CORS | README line | Description |
|-----|-----|:------------------------:|-------|------|:-----------:|-------------|
| A Bíblia Digital | https://www.abibliadigital.com.br/en | No* | Yes | No | 344 | Do not worry about managing the multiple versions of the Bible (62 chars) |
| Amanah Sunnah | https://sunnah.amanahagent.cloud/developers | `apiKey` | Yes | Yes | 345 | Semantic search across Quran, Hadith, Tafsir & 18K+ Rijal narrators (67 chars) |
| Bhagavad Gita | https://docs.bhagavadgitaapi.in | `apiKey`** | Yes | Yes** | 346 | Open Source Shrimad Bhagavad Gita API including 21+ authors translation in Sanskrit/English/Hindi (97 chars) |

\* Upstream README lists `` `apiKey` ``; historical documentation establishes `No`.
\*\* Upstream README lists `` `apiKey` `` and `Yes`; external documentation is unverified (domain for sale).

## Contribution rules discovered

From `CONTRIBUTING.md`:

- **Auth** allowed values: `OAuth`, `apiKey`, `X-Mashape-Key`, `No`, `User-Agent`
- **CORS** allowed values: `Yes`, `No`, `Unknown`
- **HTTPS** allowed values: `Yes`, `No`
- **Ordering**: alphabetical per section (case-insensitive)
- **Description**: must not exceed 100 characters
- **Column padding**: each column padded with one space on either side
- **Header format**: `API | Description | Auth | HTTPS | CORS |`
- **Separator format**: `|:---|:---|:---|:---|:---|`

## API verification & official documentation evidence

### 1. A Bíblia Digital

- **Documentation URL**: `https://www.abibliadigital.com.br/en`
- **Historical Access Requirements**:
  - Official historical repository documentation confirms that unauthenticated requests were permitted.
  - Unauthenticated access was subject to an IP-based rate limit of 20 requests per hour.
  - An optional user token was available free of charge to remove the rate limit, but it was **not mandatory** for accessing the API.
  - Under `CONTRIBUTING.md` standards, an API that functions without authentication is classified as `No`.
  - Therefore, the evidence-backed historical Auth value is `No`.
- **Current Service Availability (Documented Separately)**:
  - The official GitHub repository records that the website and APIs were disabled on 2026-08-01.
  - Automated network probes report the endpoint as unreachable or unverified.
  - Distinction: Current unavailability does not alter historical access classification.
- **Catalogue Discrepancy & Root README Handling**:
  - Upstream `README.md` (line 344) lists `apiKey`.
  - The checker expects the historical evidence value `No`, triggering a `wrong_auth` error on line 344 during live validation.
  - In accordance with task instructions, the root `README.md` is **kept unchanged**; the evidence-backed discrepancy is reported explicitly rather than silently editing upstream data.

### 2. Amanah Sunnah

- **Documentation URL**: `https://sunnah.amanahagent.cloud/developers`
- **Developer Documentation Verification**:
  - Requires an API key passed via the `X-API-Key` HTTP request header.
  - Registration provides free API keys.
  - Official documentation explicitly specifies: no billing, no usage caps, and no rate limits.
  - The catalogue entry lists `apiKey`, `Yes` for HTTPS, and `Yes` for CORS.
- **Verdict**:
  - Both catalogue entry and developer documentation agree (`apiKey`, `Yes`, `Yes`). Correct as-is on line 345.

### 3. Bhagavad Gita

- **Documentation URL**: `https://docs.bhagavadgitaapi.in`
- **Documentation Verification vs. Catalogue Consistency**:
  - The assigned documentation domain currently displays a parking / domain-for-sale page.
  - External documentation access requirements are formally treated as **unverified evidence**.
  - Alternative similarly named APIs (e.g. `BhagavadGita.io` or `gita-api.vercel.app`) must NOT be substituted.
  - Access requirements must not be invented, nor should the entry be deleted based on automated request failure.
  - The checker performs catalogue consistency validation (confirming the row has 5 columns, correct padding, valid allowed enum values, and matches expected task metadata) without confusing catalogue consistency with live external documentation verification.
- **Verdict**:
  - Retain README entry line 346 as-is.

## Ordering and neighbor relationships

The `### Books` section starts at line 341.
- Line 342: Table header
- Line 343: Table separator
- Line 344: `A Bíblia Digital` (casefold: `"a bíblia digital"`)
- Line 345: `Amanah Sunnah` (casefold: `"amanah sunnah"`)
- Line 346: `Bhagavad Gita` (casefold: `"bhagavad gita"`)
- Line 347: `Bhagavad Gita telugu` (casefold: `"bhagavad gita telugu"`)

Verification:
- Preceding neighbor of `A Bíblia Digital`: None (first row in section).
- Following neighbor of `A Bíblia Digital`: `Amanah Sunnah`.
- Preceding neighbor of `Amanah Sunnah`: `A Bíblia Digital`.
- Following neighbor of `Amanah Sunnah`: `Bhagavad Gita`.
- Preceding neighbor of `Bhagavad Gita`: `Amanah Sunnah`.
- Following neighbor of `Bhagavad Gita`: `Bhagavad Gita telugu`.

Alphabetical comparison:
`"a bíblia digital"` < `"amanah sunnah"` < `"bhagavad gita"` < `"bhagavad gita telugu"`

The alphabetical ordering holds case-insensitively across all entries in the `Books` section.
No ordering violations exist in the upstream `Books` section.

## Live validation behavior & exit code

Running live validation against `README.md` (`python3 tools/course_checks/r02-t039.py`):
- All 26 rows in `### Books` satisfy table structure, column count, delimiter padding, and alphabetical ordering.
- Selected-entry ordering and neighbor ordering pass (`[OK]`).
- Task-specific validation identifies one evidence-backed discrepancy on line 344:
  `line 344 'A Bíblia Digital' auth='apiKey' https='Yes' cors='No' [ERROR]`
  `wrong_auth: 'A Bíblia Digital' field 'auth': expected 'No', got 'apiKey'`
- Exit code: `1` (reflecting the uncorrected upstream discrepancy on A Bíblia Digital).
- This exit code and error report transparently document the discrepancy without modifying the base repository.
