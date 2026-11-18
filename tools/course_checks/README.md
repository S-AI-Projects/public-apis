# Course Checks

## R02-T046 — Classify failures correctly: Dictionaries [README.md]

### Purpose
Distinguishes HTTP 200, 403, 404, 429, HEAD-405/GET-fallback, timeout, and DNS failure.
Ensures that transient network errors, rate limits, or forbidden responses are not falsely marked as missing resources.

### Selected Entries
- [Chinese Character Web](http://ccdb.hemiola.com/) (line 901)
- [Chinese Text Project](https://ctext.org/tools/api) (line 902)
- [Collins](https://api.collinsdictionary.com/api/v1/documentation/html/) (line 903)

### Usage
From repository root:
```bash
python3 tools/course_checks/r02-t046.py
python3 tools/course_checks/r02-t046.py --self-test
```

### Offline Fixtures
- `01_http_200.json`: Success (200)
- `02_http_404.json`: Missing resource (404)
- `03_http_429.json`: Rate limited (429)
- `04_http_403.json`: Forbidden (403)
- `05_head_405_get_200.json`: Method Not Allowed fallback to GET (200)
- `06_timeout.json`: Connection / Read Timeout
- `07_dns_failure.json`: Domain resolution failure
