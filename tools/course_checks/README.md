# Course Checks

Offline validation scripts for assigned Public APIs repository tasks.

## R02-T021: Currency Exchange Parser

### Purpose

Extract selected API entries from the `Currency Exchange` category in the main `README.md` while preserving their original line numbers.

### Selected APIs

| API | URL | Description | Auth | HTTPS | CORS | Original README line |
|---|---|---|---|---|---|---:|
| Currencylayer | https://currencylayer.com | Exchange rates and currency conversion | apiKey | Yes | Unknown | 609 |
| Exchangerate.host | https://exchangerate.host | Foreign exchange & crypto rates API (keyless access ended 2023) | apiKey | Yes | Unknown | 610 |
| Exchangeratesapi.io | https://exchangeratesapi.io | Exchange rates with currency conversion | apiKey | Yes | Yes | 611 |

### Extracted Fields

- API display name
- URL, including URL fragments
- Description
- Authentication method
- HTTPS availability
- CORS availability
- Category
- Original README line number

### Run the Parser

From the repository root:

```bash
python3 tools/course_checks/r02-t021.py