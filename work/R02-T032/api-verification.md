# R02-T032 — Official documentation verification

- **Date (UTC):** 2026-11-16
- **Pinned README:** `2676ca49d557ef14a0f478311506dae947639028`
- **Method:** official service website and official API documentation pages
  were fetched directly. No API keys were used and no authenticated API call
  was attempted.

This document separates:

- **Facts** — stated on the official page or directly observed over HTTP.
- **Inferences** — reasonable conclusions drawn from those facts.
- **Unknown / not verified** — information the available official material did
  not establish.

No README row was changed. The reasons are recorded per entry and summarised at
the end.

---

## 1. BaconMockup

**Official source:** `https://baconmockup.com/` (fetched 2026-11-16)

### Facts

- The page describes "A simple way to use pictures of tasty meat as
  placeholders in your design."
- The documented usage is: "Just put your image width and height in our url
  and you'll get some meat."
- The page gives the example `https://baconmockup.com/300/200`.
- The page links to a GitHub project and to an image-attribution page.
- No API key, account registration, token or authentication header is
  mentioned on the page.
- The official URL is served over HTTPS.

### Inferences

- The README description "Resizable bacon placeholder images" is consistent
  with the official width/height URL behaviour.
- `Auth = No` is consistent with the absence of any documented key or account
  requirement.
- `HTTPS = Yes` is directly supported by the official URL and example.
- The assigned URL is the official service homepage, not a separate API
  endpoint or documentation page.

### Unknown / not verified

- CORS support is **not documented** on the official page. The README value
  `CORS = Yes` was not independently confirmed and was therefore preserved.
  Opening a page in a browser is not evidence of API CORS support.
- The live check confirms only that the homepage returned HTTP 200 directly.
  It does not prove that every image-size route is available.

### Live observation

`OK`, HTTP 200, no redirects, final URL `https://baconmockup.com/`, one
request. See `live-results.json`.

### README verdict

No change. The official identity, description, auth and HTTPS fields are
consistent with the assigned URL. CORS is unverified but not contradicted.

---

## 2. CalorieNinjas

**Official source:** `https://calorieninjas.com/api` (fetched 2026-11-16)

### Facts

- The page title is "API Documentation".
- It states: "To use the CalorieNinjas API, you need to sign up for a free
  account and get an API key."
- The documented endpoint is `HTTP GET`
  `https://api.calorieninjas.com/v1/nutrition?query=`.
- The documentation lists `X-Api-Key` as a required header and says it is the
  "API Key associated with your account."
- The page also documents `/v1/imagetextnutrition` and `/v1/recipe`.
- The page displays a prominent migration notice:
  - "CalorieNinjas Is Migrating To API Ninjas"
  - "CalorieNinjas is being turned down this year, but don't worry! You can
    find our Nutrition and Recipe APIs are API Ninjas, which contains a massive
    collection of over 80 different APIs."
  - The notice links to `https://api-ninjas.com`.
- The official CalorieNinjas pages and API examples use HTTPS.

### Inferences

- The README description "Nutrition and calorie data for foods and recipes"
  is consistent with the documented nutrition and recipe endpoints.
- `Auth = apiKey` is directly supported by the required `X-Api-Key` header.
- `HTTPS = Yes` is supported by the official examples and `api.` endpoint.
- The assigned URL is the official API documentation page, not a standalone
  API endpoint.
- The migration notice is an official vendor statement. It is not an HTTP
  redirect, and the CalorieNinjas documentation and assigned URL remain live.

### Unknown / not verified

- CORS support is **not documented** on the API page. The README value
  `CORS = Yes` was not independently confirmed and was therefore preserved.
- The migration notice does not state a precise shutdown date in the fetched
  text. The page still documents CalorieNinjas endpoints and still returns
  HTTP 200.
- No live API endpoint was called, so the current runtime availability of
  `api.calorieninjas.com` was not tested.
- API Ninjas is a separate product and platform. Its Nutrition API is
  documented at `https://api-ninjas.com/api/nutrition`, but replacing the
  CalorieNinjas row with API Ninjas would change service identity, not merely
  correct a broken redirect.

### Live observation

`OK`, HTTP 200, no redirects, final URL `https://calorieninjas.com/api`, one
request. See `live-results.json`.

### README verdict

No change. The assigned URL is still the official, live CalorieNinjas API
documentation page and was reached without a redirect. The migration notice is
recorded as a follow-up item for maintainers, but it does not justify changing
the URL inside a redirect-verification task: the notice is not a redirect, and
API Ninjas is a different service identity. Any migration of the catalogue row
should be a separate, explicitly reviewed change.

---

## 3. Chomp

**Official sources:**

- `https://chompthis.com/api/` (fetched 2026-11-16)
- `https://chompthis.com/api/v2/docs/` (fetched 2026-11-16)

### Facts

- The official page describes Chomp as "The Ultimate Food & Nutrition API" and
  advertises "high-quality data on over 1.2 million grocery products, branded
  foods, and raw ingredients."
- The page offers "Get API Key", "Log In" and "Read the Docs".
- The linked documentation is `https://chompthis.com/api/v2/docs/`.
- The documentation says the base URL is `https://chompthis.com/api/v2`.
- The documentation instructs users to open an endpoint and use its
  "Authenticate" control before sending a live request; the landing page also
  provides "Get API Key".
- The official pages and API base URL use HTTPS.

### Inferences

- The README description "Data about various grocery products and foods" is
  consistent with the official product, branded-food and ingredient data.
- `Auth = apiKey` is supported by the documented API-key acquisition and
  authentication flow.
- `HTTPS = Yes` is supported by the official pages and API base URL.
- The assigned URL is the official API landing/pricing page; the full reference
  is at `/api/v2/docs/`.

### Unknown / not verified

- CORS support is **not documented** on the landing page or the documentation
  page. The README value `CORS = Unknown` was preserved; no evidence was found
  that would justify changing it to `Yes` or `No`.
- No live API endpoint was called, so endpoint availability, authentication
  success and response schemas were not tested.

### Live observation

`OK`, HTTP 200, no redirects, final URL `https://chompthis.com/api/`, one
request. See `live-results.json`.

### README verdict

No change. The official identity, description, auth and HTTPS fields are
consistent with the assigned URL and its linked documentation. CORS remains
unknown, matching the existing README value.

---

## Summary

| Entry | Official identity | URL role | Description | Auth | HTTPS | CORS | README change |
|---|---|---|---|---|---|---|---|
| BaconMockup | `baconmockup.com` | Service homepage | Supported | `No` supported | `Yes` supported | `Yes` not documented | None |
| CalorieNinjas | `calorieninjas.com` | API documentation page | Supported | `apiKey` supported (`X-Api-Key`) | `Yes` supported | `Yes` not documented | None |
| Chomp | `chompthis.com` | API landing/pricing page | Supported | `apiKey` supported | `Yes` supported | `Unknown` preserved | None |

### Follow-up observation

CalorieNinjas officially announces a migration to API Ninjas. This is recorded
for maintainers, but no README edit was made because:

1. the assigned CalorieNinjas URL returned HTTP 200 directly with no redirect;
2. the page still serves the official CalorieNinjas API documentation;
3. API Ninjas is a different service identity, so replacing the row would be a
   catalogue migration rather than a redirect correction; and
4. this task is scoped to redirect-chain verification and preservation of the
   existing README fields unless reliable evidence clearly requires a change.

No entry was removed. No entry was added. No API key, secret or authenticated
request was used.
