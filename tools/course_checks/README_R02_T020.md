# Course Check Tool: R02-T020 (Check the List’s Formatting: Anime)

## Overview
This tool validates Markdown table syntax, heading hierarchy, segment spacing, and alphabetical ordering rules for the `Anime` section of `README.md` in accordance with repository contribution guidelines. It preserves non-English text (Unicode) and Markdown links, and reports source line numbers for any malformed syntax.

## Selected Entries
1. **AniAPI**
   - URL: `https://aniapi.com/docs/`
   - Category: `Anime`
   - Line: 216
2. **AniDB**
   - URL: `https://wiki.anidb.net/HTTP_API_Definition`
   - Category: `Anime`
   - Line: 217
3. **AniList**
   - URL: `https://github.com/AniList/ApiV2-GraphQL-Docs`
   - Category: `Anime`
   - Line: 218

## Usage
- Run offline self-test assertions:
  ```bash
  python3 tools/course_checks/r02-t020.py --self-test
  ```
- Validate an entire markdown file or section:
  ```bash
  python3 tools/course_checks/r02-t020.py --check-file README.md
  ```

## Acceptance Criteria
- [x] Malformed fixtures rejected with exact source line numbers.
- [x] Valid non-English text and Markdown links preserved.
- [x] Proposed edits obey the repository's documented alphabetical order.
- [x] Self-test exits non-zero on assertion failures.
- [x] Retention policy enforced.
