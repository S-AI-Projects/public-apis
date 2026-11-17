# Course Checks

## R02-T035 — News metadata

### Purpose
Check the three assigned News APIs and their required `Auth`, `HTTPS`, and `CORS` metadata.

### Selected APIs
- [Mediastack](https://mediastack.com) — News
- [Associated Press](https://developer.ap.org/) — News
- [Chronicling America](https://www.loc.gov/apis/additional-apis/chronicling-america-api/) — News

### Expected README values
| API | Auth | HTTPS | CORS |
|:---|:---|:---|:---|
| Mediastack | `apiKey` | Yes | Yes |
| Associated Press | `apiKey` | Yes | Unknown |
| Chronicling America | No | Yes | Unknown |

### Run the checker
```bash
python3 tools/course_checks/r02-t035.py
```

The checker reads only the `### News` table, reports original README line numbers, and exits non-zero if a selected entry is missing or its required metadata is missing, malformed, or unexpected.

### Run offline tests
```bash
python3 tools/course_checks/r02-t035.py --self-test
```

### Fixtures
- `valid.md`: all three entries with valid metadata, plus a decoy outside News
- `missing-field.md`: missing `Auth` value
- `missing-entry.md`: missing Associated Press entry
- `invalid-value.md`: invalid `CORS` value

### Results
- All 4 offline fixture tests passed, including exact-error and non-zero-exit assertions.
- All 3 selected APIs were found in News at lines 1854–1856.
- README metadata now passes the check.
- Chronicling America CORS remains `Unknown`: the collection endpoint returned an inconclusive HTTP 403 without a CORS header.
