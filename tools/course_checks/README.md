# R02-T050 — Redirect Verification: Anti-Malware

## Purpose

Verifies redirect chains for the **Anti-Malware** section of `README.md`.
Resolves each assigned URL with a bounded request budget (HEAD, max 10 hops, 10s timeout),
classifying each result as: `ok`, `redirect`, `loop`, `login_wall`, `timeout`, or `error`.
Distinguishes moved resources from redirect loops, transient failures, and login walls.

## Assigned Entries

| Line | API Name | URL |
|------|----------|-----|
| 244 | AbuseIPDB | https://docs.abuseipdb.com/ |
| 245 | AlienVault Open Threat Exchange (OTX) | https://otx.alienvault.com/api |
| 246 | CAPEsandbox | https://capev2.readthedocs.io/en/latest/usage/api.html |

## Usage

```bash
# Offline self-test (uses JSON fixtures, no network)
python3 tools/course_checks/r02-t050.py --self-test

# Live redirect verification (makes HEAD requests, timeout=10s)
python3 tools/course_checks/r02-t050.py
```

## Fixtures (`work/R02-T050/fixtures/`)

| File | Description | Expected classification |
|------|-------------|------------------------|
| `direct-200.json` | Single hop, HTTP 200 — resource found directly | `ok` |
| `redirect-301.json` | 301 permanent redirect followed by 200 | `redirect` |
| `redirect-loop.json` | Repeated URL in chain — loop detected | `loop` |
| `timeout.json` | Status 0 — connection timed out | `timeout` |

## Classification Logic

| Classification | Condition |
|---------------|-----------|
| `ok` | Final status 200, single hop |
| `redirect` | At least one 3xx hop before final 200 |
| `loop` | URL repeated in chain, or > 10 hops |
| `login_wall` | Final status 401 or 403 |
| `timeout` | Status 0 (OSError / connection refused) |
| `error` | Any other final status (e.g. 404, 500) |

## Notes

- AlienVault OTX URL (`/api` path) returned HTTP 404 from an automated HEAD request.
  The OTX platform (`https://otx.alienvault.com`) returns 200 — service is live.
  Per project policy, the entry is NOT removed based on a single automated failure.
  Labelled unverified; human browser verification recommended.
- AbuseIPDB and CAPEsandbox returned HTTP 200 directly.
- No README.md changes were made.
- Requests use a 10-second timeout and HEAD method (falling back to GET on 405).
