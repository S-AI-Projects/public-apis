# Category Consistency Checker (`r02-t053.py`)

## Overview

`r02-t053.py` is a specialized, standard-library tool developed for Task **R02-T053** (Issue #53) on `README.md`. It validates markdown heading hierarchies, heading duplicate/misplacement anomalies, and entry category consistency without relying on fragile keyword matching.

## Category Rules

1. **Heading Hierarchy and Ordering**:
   - Level 3 headings (`### <Category>`) define API categories.
   - Categories must strictly follow case-insensitive alphabetical ordering.
   - Duplicate headings (identical normalized titles appearing more than once in the document) are disallowed and flagged.
2. **Category Consistency & Reclassification Guardrails**:
   - **No Keyword Reclassification**: An entry must NEVER be reclassified or moved solely due to substring or keyword matches in its name or description (e.g. words like "Validation" or "Data").
   - **Citation Requirement**: A proposed move or misplacement flag requires a verified subject citation derived from official documentation.
   - **Conservative Recommendations**: Without a verified citation, entries default to `keep`. If a cited subject maps to an alternate category, the tool outputs `manual_review` with `proposed_category`.
   - **Safe Read-Only Operation**: The checker never automatically modifies `README.md` and never recommends deleting a link.

## What Counts as a Flag

- **Repeated Heading**: Same heading title found at multiple lines in `README.md`.
- **Misplaced Heading**: A category heading appearing out of alphabetical sequence relative to preceding category headings.
- **Misplaced Entry (`manual_review`)**: An entry whose verified subject citation maps to a category different from the section it currently resides in.
- **Rejected Proposed Move**: Any proposed move submitted without a complete official documentation citation.

## Evidence-Citation Format

Any subject citation must adhere to the following JSON schema:

```json
{
  "observed_subject": "<primary subject observed in official documentation>",
  "citation_url": "<URL of official documentation where subject was confirmed>",
  "observation_date": "<YYYY-MM-DD>"
}
```

Required fields:
- `observed_subject`: Concrete subject string matching known category taxonomy.
- `citation_url`: Live documentation URL verified via observation.
- `observation_date`: Date the documentation page was inspected.

## Explicit Subject-to-Category Mapping

The tool employs an explicit dictionary mapping verified subjects to categories:

| Observed Subject | Target Category |
|---|---|
| `phone number validation and carrier lookup` | `Phone` |
| `phone number validation` | `Phone` |
| `phone number standardization and validation` | `Phone` |
| `validate and standardize phone numbers` | `Phone` |
| `phone number validation & carrier lookup` | `Phone` |
| `phone specifications` | `Phone` |
| `place phone calls` | `Phone` |
| `caller id and lrn lookup` | `Phone` |
| `weather forecasts and meteorological data` | `Weather` |
| `weather` | `Weather` |
| `books catalog` | `Books` |
| `animal pictures and facts` | `Animals` |
| `photo editing and image processing` | `Photography` |
| `foreign exchange rates and currency conversion` | `Currency Exchange` |
| `ip geolocation and threat intelligence` | `Anti-Malware` |
| `vat number validation` | `Data Validation` |
| `address verification` | `Data Validation` |

## Selected Entries for Task R02-T053

Located under `### Phone` (lines 2037–2048):

1. **Numlookup** (Line 2040)
   - URL: `https://numlookupapi.com`
   - Description: `Phone number validation and carrier lookup API with global coverage`
   - Verified Subject: `phone number validation and carrier lookup` (Carrier & line type lookup, E.164 validity check)
   - Evaluation: Aligns with `Phone` -> Recommendation: `keep`
2. **Numverify** (Line 2041)
   - URL: `https://numverify.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers`
   - Description: `Phone number validation`
   - Verified Subject: `phone number validation` (Global phone number validation, carrier lookup, numbering plans)
   - Evaluation: Aligns with `Phone` -> Recommendation: `keep`
3. **Cloudmersive Validate** (Line 2042)
   - URL: `https://cloudmersive.com/phone-number-validation-API`
   - Description: `Validate international phone numbers`
   - Verified Subject: `validate and standardize phone numbers` (International phone number auto-validation and standardization)
   - Evaluation: Aligns with `Phone` -> Recommendation: `keep`

## CLI Usage

### Self-Test & Subprocess Negative Test
```bash
python3 tools/course_checks/r02-t053.py --self-test
```

### Standalone Negative Test
```bash
python3 tools/course_checks/r02-t053.py --negative-test
```

### Run on Selected Entries
```bash
python3 tools/course_checks/r02-t053.py --readme README.md --section Phone --selected-only --citations work/R02-T053/citations.json
```

### Run on Full Section & Document Headings
```bash
python3 tools/course_checks/r02-t053.py --readme README.md --section Phone --citations work/R02-T053/citations.json --output-json work/R02-T053/report_full_section.json --output-text work/R02-T053/report_full_section.txt
```
