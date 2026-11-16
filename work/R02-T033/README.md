# R02-T033 — Conservative Duplicate URL Detection

## Objective

Check the assigned APIs in the repository's Environment section for exact URL duplicates and conservative URL-normalization matches.

## Scope

Only the Environment section of the root `README.md` is in scope.

Assigned entries:

| API | Source line |
|---|---:|
| AirNow | 1058 |
| BreezoMeter Pollen | 1059 |
| Calendrier Tempo | 1060 |

The checker scans the Environment section and preserves each entry's API name, source line number, URL, and original Markdown row.

## Detection rules

The checker reports:

1. Exact URL-string duplicates.
2. Conservative normalization matches, including scheme and hostname case differences and default-port differences.

Normalization does not intentionally merge URLs with different paths, trailing slashes, non-default ports, query strings, or fragments. Reserved percent-encoded characters are not decoded.

## Safety

- The checker is read-only and does not modify the catalogue.
- It does not delete, merge, or automatically recommend removing entries.
- Every reported match requires manual review.
- The checker uses Python's standard library and makes no network requests.

## Validation

The offline self-test suite contains 34 checks and passed in normal, optimized (-O), and maximum-optimization (-OO) Python execution modes.

The real catalogue scan examined 33 Environment entries and reported no exact duplicates or conservative normalization matches.

Detailed inputs, expected results, actual results, runtime information, API documentation verification, and validation logs are stored alongside this file.
