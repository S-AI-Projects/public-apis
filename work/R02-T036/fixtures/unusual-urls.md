# R02-T036 fixture: unusual URL characters

### Vehicle
API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [Auto Body Shop Directory](https://autobodyshopnear.com/developers/body-shop-api) | Find auto body shops by ZIP code, city, location, or profile | No | Yes | No |
| [Bike Reliability](https://bikereliability.co.uk/developers) | UK motorcycle reliability ranked by first-time MOT pass rates | No | Yes | Yes |
| [BoltPatternHQ](https://boltpatternhq.com/mcp/) | Vehicle wheel fitment, bolt pattern (PCD), offset, and center bore specifications | No | Yes | Yes |
| [Query API](https://example.com/search?q=wheel&size=17&page=1) | Query parameters in URL | No | Yes | Yes |
| [Encoded API](https://example.com/docs/a%20b/%28c%29?next=%2Fhome) | Percent-encoded characters in URL | No | Yes | Unknown |
| [Paren API](https://example.com/docs/API_(v2)) | Balanced parentheses in URL | No | Yes | Yes |
| [Angle API](<https://example.com/docs/angle_(v1)>) | Angle-bracket Markdown destination | No | Yes | Yes |
| [Fragment API](https://example.com/docs/page#section-2) | Fragment in URL with escaped pipe \| and code `a|b` | No | Yes | Yes |
| [Titled API](https://example.com/docs/API_(v3) "Documentation") | Markdown link title after a parenthesized URL | No | Yes | Yes |
| [Escaped Paren API](https://example.com/docs/API_\(v4\)) | Backslash-escaped parentheses in URL | No | Yes | Yes |
| [Pipe API](https://example.com/docs/a|b) | Literal pipe inside the link destination | No | Yes | Yes |

**[⬆ Back to Index](#index)**
