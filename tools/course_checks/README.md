# Course Checkers

This directory contains standalone, standard-library Python checkers used for coursework validation.

## R02-T042 — Conservative Duplicate URL Detection: Open Data [README.md]

Run the checker from the repository root:

    python3 tools/course_checks/r02-t042.py

Run deterministic offline tests:

    python3 tools/course_checks/r02-t042.py --self-test

The checker examines the `Open Data` API catalogue section in `README.md` and reports:

- Exact URL-string duplicates.
- Conservative normalization matches, such as scheme/hostname case differences and default-port differences.
- Original API names, source line numbers, and Markdown rows.

It preserves query strings, fragments, paths, trailing slashes, non-default ports, and reserved percent-encoded characters as distinct.

It does not modify the catalogue or automatically delete entries. Every potential duplicate requires manual review.

The checker uses only the Python standard library. Live API documentation verification is recorded separately in the task evidence.
