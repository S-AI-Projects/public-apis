# API Documentation Verification — R02-T033

Verification date: 17 November 2026

This document records findings from the providers' documentation. It does not infer CORS support from HTTPS availability or public access.

## 1. AirNow

Assigned documentation:
https://docs.airnowapi.org/

Official source checked:
https://docs.airnowapi.org/faq
https://docs.airnowapi.org/docs/AirNowAPIFactSheet.pdf

Findings:
- Authentication: API key required. The official FAQ explains where users can find their API key, and the fact sheet says an AirNow API account is required.
- HTTPS: The assigned documentation URL uses HTTPS.
- CORS: Not confirmed by the sources checked.

README comparison:
- Auth: apiKey — supported.
- HTTPS: Not independently verified — the assigned documentation URL uses HTTPS, but that alone does not establish the API endpoint's protocol support.
- CORS: Yes — not independently verified in this check.

## 2. BreezoMeter Pollen

Assigned documentation:
https://docs.breezometer.com/api-documentation/pollen-api/v2/

Observed redirect:
The assigned legacy URL redirects to Google Maps Platform.

Current official Google documentation checked:
https://developers.google.com/maps/documentation/pollen/get-api-key
https://developers.google.com/maps/documentation/pollen/web-service-best-practices

Findings:
- Authentication: Current Google Pollen API documentation requires authentication and documents API key setup.
- HTTPS: Google states that HTTPS is required for Google Maps Platform requests using API keys or user data.
- CORS: Not confirmed by the sources checked.
- Legacy compatibility: The redirect means the current Google documentation should not be treated as proof that every legacy BreezoMeter endpoint or behavior remains unchanged.

README comparison:
- Auth: apiKey — consistent with current Google Pollen API guidance, with the legacy redirect caveat above.
- HTTPS: Yes — current Google Pollen API guidance requires HTTPS.
- CORS: Unknown — not independently verified.

## 3. Calendrier Tempo

Assigned documentation:
https://www.calendrier-tempo.fr/api-tempo

Official source checked:
https://www.calendrier-tempo.fr/api-tempo

Findings:
- Authentication: No API key required. The provider explicitly says the API is free and available without registration or a key.
- HTTPS: Yes. The provider documents HTTPS API endpoints and HTTPS curl examples.
- CORS: Not explicitly confirmed by the documentation inspected.

README comparison:
- Auth: No — supported.
- HTTPS: Yes — supported.
- CORS: Yes — not independently verified in this check.

## Verification limitations

- No live API requests were made as part of this documentation review.
- CORS was not marked confirmed without explicit provider documentation.
- A documentation URL using HTTPS does not by itself establish that every API endpoint supports HTTPS or browser cross-origin requests.
- The BreezoMeter legacy documentation redirect is recorded as a compatibility caveat, not as proof that the old API is still available.
- These findings do not justify deleting or changing any catalogue entry automatically.
