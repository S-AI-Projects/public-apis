# Course Checks

## R02-T043 — Category Consistency: Personality [README.md]

### Purpose
Check whether selected APIs are placed under the correct README category (`Personality`), and detect misplaced entries, repeated headings, or missing entries without reclassifying entries solely based on keywords.

### Selected APIs
- [Advice Slip](http://api.adviceslip.com/) — Personality (line 2005)
- [Astro Agents](https://astro-agent.dev/llms.txt) — Personality (line 2006)
- [AstroWay](https://api.astroway.info/docs/) — Personality (line 2007)

### Run the checker
```bash
python3 tools/course_checks/r02-t043.py
```

### Run offline tests
```bash
python3 tools/course_checks/r02-t043.py --self-test
```

### Fixtures
- `valid.md`: correct category placement
- `misplaced.md`: misplaced API entries
- `repeated-heading.md`: duplicate category heading
- `missing-entry.md`: missing API entry

### Results
- All 4 offline fixture tests passed.
- All 3 selected APIs were found under `Personality`.
- No README category correction was required.
