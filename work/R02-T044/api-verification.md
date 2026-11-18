# API Verification & Evidence Table: Cryptocurrency (R02-T044)

## Evidence Table

| API Name | Documentation / Source URL | Field | Stored / Observed Value | Expected / Proposed Value | Evidence Notes |
|:---|:---|:---|:---|:---|:---|
| Coinlayer | `https://coinlayer.com` | Auth | `apiKey` | `apiKey` | Free API key required for live endpoints. |
| Coinlayer | `https://coinlayer.com` | HTTPS | Yes | Yes | Endpoints support HTTPS. |
| Coinlayer | `https://coinlayer.com` | CORS | Unknown | Unknown | Browser CORS headers not officially documented. |
| 0x | `https://docs.0x.org/` | Auth | No | No | Free open public API access for basic querying. |
| 0x | `https://docs.0x.org/` | HTTPS | Yes | Yes | HTTPS endpoints documented. |
| 0x | `https://docs.0x.org/` | CORS | Yes | Yes | Verified support for client-side web3 queries. |
| 1inch | `https://business.1inch.com/portal/documentation` | Auth | `apiKey` | `apiKey` | API key required via developer portal. |
| 1inch | `https://business.1inch.com/portal/documentation` | HTTPS | Yes | Yes | HTTPS endpoints documented. |
| 1inch | `https://business.1inch.com/portal/documentation` | CORS | Unknown | Unknown | CORS headers not explicitly guaranteed. |

## Verification Summary
- No proposed changes to catalogue values: all 3 entries in `README.md` match their observed official documentation and metadata schema.
- All 3 documentation URLs are reachable (HTTP 200).
- No catalogue entries were deleted or modified.
