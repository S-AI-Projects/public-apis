# Course Checkers

## R02-T045 — Make checks work offline: Music [README.md]

### Purpose
Builds a fixture-based offline test suite for parsing and validating the Music category in `README.md`.
Live network availability checks remain optional and separate.

### Selected Entries
- [7digital](https://docs.7digital.com/reference) (line 1810) — `OAuth` | HTTPS: Yes | CORS: Unknown
- [AI Mastering](https://aimastering.com/api_docs/) (line 1811) — `apiKey` | HTTPS: Yes | CORS: Yes
- [Audiomack](https://www.audiomack.com/data-api/docs) (line 1812) — `OAuth` | HTTPS: Yes | CORS: Unknown

### Usage
From repository root:
```bash
python3 tools/course_checks/r02-t045.py
python3 tools/course_checks/r02-t045.py --self-test
```

### Offline Fixtures
- `valid.md`: Clean valid table rows for assigned entries
- `malformed.md`: Malformed table rows (missing columns, non-markdown link in API cell)
- `unusual-urls.md`: URLs with query strings, percent-encoding, and fragments
