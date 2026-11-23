# R02-T060: Repeatable maintenance report — Anime

**Selected entries:** AniAPI, AniDB, AniList.

## Run

```sh
python3 tools/course_checks/r02-t060.py --self-test
python3 tools/course_checks/r02-t060.py --report --readme README.md --output work/R02-T060/actual.json
```

The self-test is offline, uses Python's standard library and exits non-zero if an assertion fails. The checker is scoped to the assigned README section. Automated failures are not sufficient grounds to remove an API.

## Evidence scope

Stable before/after metadata and manual decision report with source lines

## Selected source URLs

- https://aniapi.com/docs/
- https://wiki.anidb.net/HTTP_API_Definition
- https://github.com/AniList/ApiV2-GraphQL-Docs

