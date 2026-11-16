# Course Checkers

This directory contains standalone, standard-library Python checkers used for coursework validation.

## R02-T033 — Conservative Duplicate URL Detection

Run the checker from the repository root:

    python3 tools/course_checks/r02-t033.py

Run deterministic offline tests:

    python3 tools/course_checks/r02-t033.py --self-test
    python3 -O tools/course_checks/r02-t033.py --self-test
    python3 -OO tools/course_checks/r02-t033.py --self-test

The checker examines only the assigned API catalogue section and reports:

- Exact URL-string duplicates.
- Conservative normalization matches, such as scheme/hostname case differences and default-port differences.
- Original API names, source line numbers, and Markdown rows.

It preserves query strings, fragments, paths, trailing slashes, non-default ports, and reserved percent-encoded characters.

It does not modify the catalogue or recommend automatic deletion. Every potential duplicate requires manual review.

The checker uses only the Python standard library and performs no network requests. Live API documentation verification is recorded separately in the task evidence.
