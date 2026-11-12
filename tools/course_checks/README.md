# Course Checkers

## R02-T023 — Personality Duplicate Detection

This checker implements conservative duplicate URL detection for the assigned Personality API entries.

### Selected README entries

| API | README line | Listed URL |
|---|---:|---|
| Advice Slip | 2005 | http://api.adviceslip.com/ |
| Astro Agents | 2006 | https://astro-agent.dev/llms.txt |
| AstroWay | 2007 | https://api.astroway.info/docs/ |

The checker extracts each entry's name, URL, description, authentication, HTTPS, CORS, category, and original README line number.

### Duplicate detection and URL normalization rules

The checker enforces conservative normalization to detect duplicates without merging distinct resources:

- **Exact duplicates:** Detect identical URL strings.
- **Scheme and hostname casing:** Normalized case-insensitively per RFC 3986 (e.g. `HTTPS://` -> `https://`, `ASTRO-AGENT.DEV` -> `astro-agent.dev`).
- **Default ports:** Strip default ports (HTTP 80, HTTPS 443) while preserving non-default ports (e.g. 8080, 8443).
- **Empty path vs. root path:** Safely normalize domain root empty path to `/` (e.g. `http://api.adviceslip.com` and `http://api.adviceslip.com/` match).
- **Trailing slashes:** Handled conservatively; subpath trailing slashes are preserved and not stripped (e.g. `/docs` and `/docs/` remain distinct).
- **Query parameters:** All query parameters, values, and ordering are preserved; differing parameters or ordering are never merged.
- **URL fragments:** Meaningful fragments (e.g. `#endpoints`) are preserved and keep URLs distinct; only empty fragments (`#`) are stripped.
- **Schemes:** HTTP and HTTPS are distinct schemes and never automatically merged.
- **Different paths:** Distinct paths are never merged.
- **Manual review required:** Every proposed deletion must have a manually reviewed pair; entries are never removed or merged automatically.
- **Fail-safe:** Automated request or connection failures are never used as evidence of duplication or reasons for removal.

### Running the checker

Run from the repository root:

    python3 tools/course_checks/r02-t023.py --self-test
    python3 tools/course_checks/r02-t023.py

Flags:
- `--self-test`: Runs fully offline self-tests against JSON and Markdown fixtures as well as README parsing.
- `--all`: Reports duplicate status across all entries in the Personality category.
- `--live`: Performs optional low-volume HTTP verification for the selected entries.

### Fixtures

Offline fixtures are stored in:

    tools/course_checks/fixtures/r02-t023/duplicate_cases.json
    tools/course_checks/fixtures/r02-t023/test_personality.md

They cover exact duplicates, scheme/hostname casing, default port normalization, query parameter distinctions, fragment distinctions, subpath trailing slash behavior, root path normalization, and unrelated URLs.

### Evidence

Task evidence is stored locally in:

    work/R02-T023/

The duplicate detection analysis confirmed that all three assigned entries (Advice Slip, Astro Agents, and AstroWay) are unique within the Personality category, with zero duplicate URLs detected.
