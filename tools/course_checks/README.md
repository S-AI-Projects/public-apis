# Course Checkers

## R02-T022 — Data Validation Redirect Verification

This checker verifies the availability and redirect behaviour of three Data Validation API entries assigned in the course task.

### Selected README entries

| API | README line | Listed URL |
|---|---:|---|
| VATlayer | 643 | https://vatlayer.com/?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| Attestwire | 644 | https://api.attestwire.com/docs |
| invowerk | 645 | https://invowerk.dev/docs |

The checker extracts each entry's name, URL, description, authentication, HTTPS, CORS, category, and original README line number.

### Running the checker

Run from the repository root:

    python3 tools/course_checks/r02-t022.py --self-test
    python3 tools/course_checks/r02-t022.py

The self-test uses local JSON fixtures and does not make network requests.

The live check uses an 8-second timeout and follows a maximum of 5 redirects.

### Classification

The checker distinguishes successful responses, redirects, redirect loops, redirect limits, timeouts, request errors, HTTP errors, and likely login walls.

A single automated failure is not sufficient reason to remove an API entry.

### Fixtures

Fixtures are stored in:

    tools/course_checks/fixtures/r02-t022/redirect_cases.json

They cover HTTP 200, 301-to-200, redirect loops, timeouts, and login-wall cases.

### Evidence

Task evidence is stored separately in:

    work/R02-T022/

The live observation on 2026-11-11 returned HTTP 200 for all three entries. The observed final URLs and redirect chains are recorded in actual.json.
