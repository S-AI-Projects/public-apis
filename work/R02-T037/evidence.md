# R02-T037 evidence

Date of checks: 2026-11-17 (UTC). The catalogue is pinned at commit
`2676ca49d557ef14a0f478311506dae947639028`.

Selected category: **Games & Comics** (README line 1260).

Selected entries:

| API | README line | URL |
| --- | --- | --- |
| AmiiboAPI | 1263 | https://amiiboapi.com/ |
| Animal Crossing: New Horizons | 1264 | http://acnhapi.com/ |
| Astroworld | 1265 | https://api.astroworldmc.com |

## Metadata evidence table

| API | Field | Current value | Observed value | Proposed value | Source URL | Reasoning |
| --- | --- | --- | --- | --- | --- | --- |
| AmiiboAPI | Auth | No | Official documentation: "This is a reading-only API. Only HTTP GET method is allowed by this API." and "No authentication is required to use this API." | No (unchanged) | https://amiiboapi.org/docs/ ; https://github.com/N3evin/AmiiboAPI | Official documentation and the project repository agree that no credentials are required. |
| AmiiboAPI | HTTPS | Yes | `https://amiiboapi.com/` returned HTTP 200 over HTTPS; `https://amiiboapi.org/api/amiibo/` returned HTTP 200 over HTTPS. | Yes (unchanged) | https://amiiboapi.com/ ; live curl observation 2026-11-17 | HTTPS is served successfully. |
| AmiiboAPI | CORS | Yes | `Access-Control-Allow-Origin: *` observed from `https://amiiboapi.org/api/amiibo/`; the project requirements pin `Flask-Cors==4.0.2`. | Yes (unchanged) | https://amiiboapi.org/api/amiibo/ ; https://raw.githubusercontent.com/N3evin/AmiiboAPI/master/requirements.txt | Both the implementation and a live API response support CORS. The observation came from the `.org` deployment because `.com` API paths returned 404 during this check; that is an availability inconsistency, not evidence that CORS is disabled. |
| Animal Crossing: New Horizons | Auth | No | Official repository: "The API is free and without authentification" and "No authentification is required to make requests to any of the endpoints". | No (unchanged) | https://github.com/alexislours/ACNHAPI | The official project repository explicitly documents unauthenticated access (repository is archived, but remains the authoritative documentation). |
| Animal Crossing: New Horizons | HTTPS | Yes | Official repository: endpoints "can be accessed over HTTP or HTTPS". | Yes (unchanged) | https://github.com/alexislours/ACNHAPI | HTTPS support is documented explicitly in the official project repository (archived). The live service did not respond during the check, but there is no evidence HTTPS was withdrawn. |
| Animal Crossing: New Horizons | CORS | Unknown | No official CORS statement was found. Live HTTP and HTTPS requests received empty replies, so no `Access-Control-Allow-Origin` header could be observed. | Unknown (unchanged) | https://github.com/alexislours/ACNHAPI | Evidence is inconclusive. Changing this field to Yes or No would not be supported; preserve `Unknown`. |
| Astroworld | Auth | No | Official page: "Free, public Minecraft data API. JSON responses, CORS enabled, no auth required." | No (unchanged) | https://api.astroworldmc.com | Official documentation explicitly states no authentication is required. |
| Astroworld | HTTPS | Yes | Official base URL is `https://api.astroworldmc.com`; `/api/health` returned HTTP 200 over HTTPS. | Yes (unchanged) | https://api.astroworldmc.com ; live curl observation 2026-11-17 | Documentation and a live HTTPS response agree. |
| Astroworld | CORS | Yes | Official page: CORS enabled, and all routes send `Access-Control-Allow-Origin: *`; live `/api/health` returned `access-control-allow-origin: *`. | Yes (unchanged) | https://api.astroworldmc.com ; live curl observation 2026-11-17 | Documentation and observed response headers agree. |

## Availability observations (not metadata proof)

These observations are recorded separately from the metadata table.

| API | Observation | Interpretation |
| --- | --- | --- |
| AmiiboAPI | The checker's first HEAD request to `https://amiiboapi.com/` timed out after 10 seconds; a later live run returned HTTP 200 for HEAD. A manual curl GET to the homepage returned HTTP 200. `https://amiiboapi.com/api/amiibo...` returned HTTP 404, while the `https://amiiboapi.org` deployment returned HTTP 200 with CORS headers. | Inconsistent availability/HEAD behaviour. Not enough evidence to remove the entry or change its metadata. Preserve. |
| Animal Crossing: New Horizons | DNS resolves (`acnhapi.com` -> `162.4.84.240`), but HTTP/1.1 GET over both HTTP and HTTPS received "Empty reply from server"; the checker's HEAD received `RemoteDisconnected` and classified it as `Network Error`. | The service may be temporarily down or permanently retired. A single automated failure is not proof of removal; manual confirmation and service-status evidence would be required. Preserve. |
| Astroworld | HEAD to `https://api.astroworldmc.com` returned HTTP 200 (`Success`); `/api/health` returned HTTP 200 with a healthy JSON status. | Available at check time. |

## Documentation-quality note

`https://amiiboapi.com/docs/` returned unrelated promotional content during
this check, so it was not used as documentation evidence. The documentation
statements were taken from the `https://amiiboapi.org/docs/` mirror and the
official `N3evin/AmiiboAPI` GitHub repository. This is noted so the source
provenance is clear; it does not justify a catalogue change by itself.

## Conclusion

No README.md corrections are supported by the evidence. All nine existing
values (`Auth`, `HTTPS`, `CORS` for three APIs) remain as catalogued. No link
was removed, and no removal is recommended from a single automated failure.
