# Course Checks

## R02-T034 — Category Consistency

### Purpose
Check whether selected APIs are placed under the correct README category.

### Selected APIs
- [AI Dev Jobs](https://aidevboard.com/openapi.yaml) — Jobs
- [AI Trainer Work](https://aitrainer.work/open-data#api) — Jobs
- [Adzuna](https://developer.adzuna.com/overview) — Jobs

### Run the checker
```bash
python3 tools/course_checks/r02-t034.py
```

### Run offline tests
```bash
python3 tools/course_checks/r02-t034.py --self-test
```

### Fixtures
- valid.md: correct category placement
- misplaced.md: misplaced API entries
- repeated-heading.md: duplicate category heading
- missing-entry.md: missing API entry

### Results
- All 4 offline fixture tests passed.
- All 3 selected APIs were found under Jobs.
- No README category correction was required.
