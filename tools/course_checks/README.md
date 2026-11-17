# Course Checks

## R02-T036

### Purpose

`r02-t036.py` validates the three R02-T036 entries in the `Vehicle` table of
`README.md`. It checks the table header and separator, row shape, required
link/description/auth/HTTPS/CORS fields, URL syntax, and the expected metadata
for the selected entries. Errors include the original README line number.

The checker uses only the Python standard library and never accesses the
network.

### Selected entries

Category: `Vehicle` (`### Vehicle` table, README lines 2651-2671).

| API | README line | Expected Auth | Expected HTTPS | Expected CORS |
| --- | ---: | --- | --- | --- |
| [Auto Body Shop Directory](https://autobodyshopnear.com/developers/body-shop-api) | 2654 | No | Yes | No |
| [Bike Reliability](https://bikereliability.co.uk/developers) | 2655 | No | Yes | Yes |
| [BoltPatternHQ](https://boltpatternhq.com/mcp/) | 2656 | No | Yes | Yes |

No README catalogue values needed correction. See
`work/R02-T036/evidence.md` for the verification notes.

### Usage

From the repository root:

```bash
python3 tools/course_checks/r02-t036.py
python3 tools/course_checks/r02-t036.py --self-test
```

The first command validates the repository `README.md` and exits non-zero if
any assertion fails. The second command runs the offline fixtures and exits
non-zero if a fixture does not produce its expected result or expected error.

Use `--readme PATH` to validate a specific fixture or alternate README file:

```bash
python3 tools/course_checks/r02-t036.py --readme work/R02-T036/fixtures/valid-all.md
```

### Fixtures

Fixtures and their explicit expected outcomes are under
`work/R02-T036/fixtures/`. `manifest.json` records each fixture's expected exit
status, table line numbers, parsed entry details, and expected error text.

| Fixture | Expected | Coverage |
| --- | --- | --- |
| `valid-all.md` | Pass | All three selected entries with correct metadata |
| `malformed-row.md` | Fail | A row with four cells instead of five |
| `missing-entry.md` | Fail | Bike Reliability missing from the table |
| `missing-required-field.md` | Fail | Empty required description |
| `unusual-urls.md` | Pass | Query parameters, percent encoding, balanced and backslash-escaped parentheses, angle brackets, fragments, escaped pipes, code spans, and a Markdown link title |
| `query-encoded-url.md` | Pass | Valid query parameters and encoded URL characters |
| `parentheses-url.md` | Pass | Balanced parentheses in a Markdown URL |
| `wrong-metadata.md` | Fail | Incorrect selected CORS value |
| `malformed-header.md` | Fail | Header with the wrong number of columns |
| `bad-url.md` | Fail | Non-HTTP URL scheme |
| `bad-link.md` | Fail | API cell that is not a Markdown link |

### Test results

```text
$ python3 tools/course_checks/r02-t036.py --self-test
PASS valid-all.md
PASS malformed-row.md
PASS missing-entry.md
PASS missing-required-field.md
PASS unusual-urls.md
PASS query-encoded-url.md
PASS parentheses-url.md
PASS wrong-metadata.md
PASS malformed-header.md
PASS bad-url.md
PASS bad-link.md

Self-test: 11/11 fixtures passed

$ python3 tools/course_checks/r02-t036.py
README.md: Vehicle table lines 2651-2671
Selected entries:
  OK    line 2654: Auto Body Shop Directory | Auth=No | HTTPS=Yes | CORS=No
  OK    line 2655: Bike Reliability | Auth=No | HTTPS=Yes | CORS=Yes
  OK    line 2656: BoltPatternHQ | Auth=No | HTTPS=Yes | CORS=Yes

OK: Vehicle table structure valid; all 3 selected entries match expected metadata.
```
