# R02-T055: Metadata verification — Sports & Fitness

**Selected entries:** 5DollarFootball, AcesAPI, API-FOOTBALL.

## Run

```sh
python3 tools/course_checks/r02-t055.py --self-test
python3 tools/course_checks/r02-t055.py --report --readme README.md --output work/R02-T055/actual.json
```

The self-test is offline, uses Python's standard library and exits non-zero if an assertion fails. The checker is scoped to the assigned README section. Automated failures are not sufficient grounds to remove an API.

## Evidence scope

Three valid rows pass; fixture with a missing description is rejected

## Selected source URLs

- https://5dollarfootballapi.com/
- https://acesapi.com/docs
- https://www.api-football.com/documentation-v3

