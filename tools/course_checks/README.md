# Course Checks

Offline validation scripts for assigned Public APIs repository tasks.

## R02-T021: Currency Exchange Parser

### Purpose
Extract selected API entries from the Currency Exchange category while preserving original README line numbers.

### Selected APIs

| API | Original README line |
|---|---:|
| Currencylayer | 609 |
| Exchangerate.host | 610 |
| Exchangeratesapi.io | 611 |

### Extracted fields
- API display name
- URL
- Description
- Authentication method
- HTTPS availability
- CORS availability
- Category
- Original README line number

### Run the parser
    python3 tools/course_checks/r02-t021.py

### Run offline self-tests
    python3 tools/course_checks/r02-t021.py --self-test

### Test fixtures
Stored in `tools/course_checks/fixtures/r02-t021/`.

Tests cover successful parsing, line-number preservation, URL fragments, fenced code blocks, malformed rows, and missing categories.

### Implementation
Uses Python standard-library modules only. No network requests. Does not modify the main README.
