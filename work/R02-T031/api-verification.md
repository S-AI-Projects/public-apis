# R02-T031 — Official API verification

Date (UTC): 2026-11-16
Pinned README commit: `2676ca49d557ef14a0f478311506dae947639028`

Method: each selected entry was checked against its **official** documentation
or official website. No entry was added or removed on the basis of an
automated HTTP/link check. No catalogue correction was made, because none was
supported by reliable official evidence.

---

## 1. 4chan — `https://github.com/4chan/4chan-API`

**Official source:** `github.com/4chan/4chan-API` — "Documentation for 4chan's
read-only JSON API."

| README field | README value | Official evidence | Verdict |
|---|---|---|---|
| Description | "Simple image-based bulletin board dedicated to a variety of topics" | Official docs describe the read-only JSON API for `4chan.org` / `4channel.org` boards, which are image-based bulletin boards. | Supported |
| Auth | `No` | No API key, token or registration is documented; the API is public and read-only, with rate rules (max 1 request/second). | Supported |
| HTTPS | `Yes` | "Data from the 4chan API is exclusively accessible from `a.4cdn.org`, via either `http://` or `https://` protocols." All documentation examples use `https://`. | Supported |
| CORS | `Yes` | "CORS is supported from origins `boards.4chan.org` or `boards.4channel.org`, via `http://` or `https://`." | Supported, with caveat |

**Caveat:** CORS is supported, but only from 4chan's own origins. The README
`Yes` value is not wrong — CORS is officially supported — but it is
origin-restricted rather than open to arbitrary origins.

**URL check:** the README URL is the official documentation repository.

---

## 2. API Direct — `https://apidirect.io/docs`

**Official source:** `apidirect.io/docs` (Introduction and Authentication
pages).

| README field | README value | Official evidence | Verdict |
|---|---|---|---|
| Description | "Real-time social media data from X, LinkedIn, Reddit, YouTube, Instagram, TikTok, Facebook and news" | Official introduction: "search real-time data across social media and news"; supported platforms explicitly list LinkedIn, Twitter/X, Facebook, Reddit, YouTube, Instagram, TikTok, plus News. "Results are fetched in real-time." | Supported |
| Auth | `apiKey` | "All API requests require authentication using an API key passed in the `X-API-Key` header." Key format `ak_live_...`; missing/invalid key returns `401`. | Supported |
| HTTPS | `Yes` | "All API requests are made to: `https://apidirect.io`"; all examples use `https://`. | Supported |
| CORS | `Yes` | **Not documented** on the official Introduction or Authentication pages. | Not officially confirmed |

**Limitation:** the `CORS = Yes` value could not be confirmed from official
documentation. There is also no reliable evidence that it is *wrong*, so no
change was made. This is recorded as an open limitation rather than a
correction.

---

## 3. Ayrshare — `https://www.ayrshare.com`

**Official source:** `ayrshare.com` and `ayrshare.com/docs` (Quick Start,
API overview).

| README field | README value | Official evidence | Verdict |
|---|---|---|---|
| Description | "Social media APIs to post, get analytics, and manage multiple users social media accounts" | Official site: unified API to "post, schedule, and analyze content across 14+ social networks"; Analytics API for cross-network metrics; Business/Enterprise plans provide multi-user, white-label profiles ("manage multiple users"). | Supported |
| Auth | `apiKey` | "An API Key is required to authorize access to the API endpoints… Every API call must include the API Key in the Header using a `Bearer` Token." | Supported |
| HTTPS | `Yes` | All official examples call `https://api.ayrshare.com/api/...`. | Supported |
| CORS | `Yes` | **Not documented** on the official home page or Quick Start. | Not officially confirmed |

**Limitation:** same as API Direct — `CORS = Yes` could not be confirmed from
official documentation, and there is no reliable evidence that it is wrong, so
no change was made.

---

## Summary

| Entry | Live | Metadata supported | Catalogue correction |
|---|---|---|---|
| 4chan | Yes | Yes (CORS origin-restricted) | None needed |
| API Direct | Yes | Yes, except CORS unconfirmed | None made |
| Ayrshare | Yes | Yes, except CORS unconfirmed | None made |

- **No entry was removed.** All three are confirmed live and officially
  documented.
- **No entry was added.** Nothing was added to meet a quota.
- **No README catalogue lines were modified.** `README.md` is unchanged in
  this branch.
- An automated HTTP failure would not have been treated as proof that an API
  is invalid; all judgements above rest on official documentation.
