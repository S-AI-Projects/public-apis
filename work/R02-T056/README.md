# R02-T056: Offline parsing — Finance

**Selected entries:** Marketstack, Aletheia, Alpaca.

## Run

```sh
python3 tools/course_checks/r02-t056.py --self-test
python3 tools/course_checks/r02-t056.py --report --readme README.md --output work/R02-T056/actual.json
```

The self-test is offline, uses Python's standard library and exits non-zero if an assertion fails. The checker is scoped to the assigned README section. Automated failures are not sufficient grounds to remove an API.

## Evidence scope

Three valid rows and one malformed row; query-string URL characters preserved; no network

## Selected source URLs

- https://marketstack.com/?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers
- https://aletheiaapi.com/
- https://docs.alpaca.markets/us/docs/about-market-data-api

