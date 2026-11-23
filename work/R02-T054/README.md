# R02-T054: Failure classification — Art & Design

**Selected entries:** 3DTexel, Améthyste, Art Institute of Chicago.

## Run

```sh
python3 tools/course_checks/r02-t054.py --self-test
python3 tools/course_checks/r02-t054.py --report --readme README.md --output work/R02-T054/actual.json
```

The self-test is offline, uses Python's standard library and exits non-zero if an assertion fails. The checker is scoped to the assigned README section. Automated failures are not sufficient grounds to remove an API.

## Evidence scope

200 success; 404 unconfirmed; 429/403 forbidden-or-limited; HEAD 405 then GET 200 success; timeout; DNS failure

## Selected source URLs

- https://3dtexel.com/developers/#public-api
- https://api.amethyste.moe/
- https://api.artic.edu/docs/

