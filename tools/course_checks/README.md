# Course Checkers

## R02-T024 — Category Consistency

This checker validates the category consistency of API entries and the integrity of category headings in the `public-apis` README.md catalogue.

### Selected README entries

| API | README line | Listed Category | Listed URL |
|---|---:|---|---|
| mailboxlayer | 983 | Email | https://mailboxlayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| AGPC Domain Check | 984 | Email | https://guild.tradeuniquecapital.com/api |
| Atomic Mail | 985 | Email | https://atomic-mail.github.io/atomic-mail-agentic/ |

The checker extracts each entry's name, URL, description, authentication, HTTPS, CORS, category, and source line number.

### Category mapping methodology

1. **Heading and Table Extraction:** The checker parses the markdown file line-by-line, tracking active category headings (`### <Category>`) and identifying table boundaries while skipping fenced code blocks (` ``` ` or `~~~`).
2. **Heading Uniqueness Check:** Every category heading is indexed with its source line number to detect duplicated or misplaced headings across the catalogue, while non-category introductory sections (such as `APIs Covered Under APILayer Suite!`) are filtered out to preserve actual category structure.
3. **Evidence-Based Evaluation:** Each evaluated entry is mapped against an evidence registry of verified resource subjects derived from official service documentation.
4. **No Keyword Guessing:** The checker explicitly avoids classifying or moving entries based solely on textual keywords in entry titles or descriptions, preventing false-positive reclassifications (e.g., address extractors mentioning "emails").
5. **Manual Review Fallback:** If official evidence is ambiguous or missing, the entry is flagged as `manual_review_required` rather than automatically reclassified.

### What the checker detects

- **Misplaced entries:** Identifies entries whose verified subject clearly belongs in another category per official documentation.
- **Repeated headings:** Detects duplicate category headings across the document and reports both first-seen and repeated line numbers.
- **Ambiguous categorization:** Flags entries lacking verified ground-truth evidence for human inspection.
- **Source line tracking:** Accurately retains source line numbers for all detected issues and catalogue entries.

### What it deliberately does not automate

- **No automatic reclassification:** Entries are never moved automatically between categories.
- **No keyword-based classification:** Textual keyword matching (e.g., finding the word "mail" in a description) is never used as an automated basis to move an entry.
- **No link deletion:** Entries are never deleted or merged automatically.
- **No removals based on network status:** Connectivity timeouts or temporary endpoint failures are never treated as evidence of invalidity or miscategorization.

### Running self-tests

Run from the repository root:

    python3 tools/course_checks/r02-t024.py --self-test
    python3 tools/course_checks/r02-t024.py

- `--self-test`: Runs fully offline assertions against local Markdown fixtures and the repository `README.md`.
- Default mode: Analyzes the selected entries in `README.md`, prints the structured report, and saves evidence to `work/R02-T024/actual.json`.
- `--all`: Analyzes all entries in the `Email` category.

### Fixtures

Offline fixtures are located in `tools/course_checks/fixtures/r02-t024/`:
- `valid_entry.md`: Valid entry in correct category.
- `misplaced_entry.md`: Deliberately misplaced entry flagged for review.
- `repeated_headings.md`: Repeated category headings at separate line numbers.
- `valid_category_no_false_positive.md`: Valid category that must not be falsely flagged.
- `keyword_distinction.md`: Entries with cross-category keywords that must not trigger automatic reclassification.
- `ambiguous_entry.md`: Ambiguous entries requiring manual review.
- `introductory_heading.md`: Non-category introductory heading followed by a real category table.

### Evidence

Task evidence is stored locally in `work/R02-T024/`. All three selected entries were verified to be correctly placed in `Email`, with zero misplaced entries or repeated headings found in the repository catalogue.
