#!/usr/bin/env python3
"""
R02-T020: Formatting and ordering validation for Public APIs catalogue.
Category: Anime [README.md]
Task: R02-T020 · 10 of 10

Selected entries:
- AniAPI: https://aniapi.com/docs/ (Line 216)
- AniDB: https://wiki.anidb.net/HTTP_API_Definition (Line 217)
- AniList: https://github.com/AniList/ApiV2-GraphQL-Docs (Line 218)
"""

import sys
import os
import re
import json
import argparse
from typing import List, Dict, Any, Tuple

LINK_RE = re.compile(r'^\[([^\]]+)\]\((https?://[^\s)]+)\)$')
AUTH_OPTIONS = ['`apiKey`', '`OAuth`', '`X-Mashape-Key`', '`User-Agent`', 'No']
HTTPS_OPTIONS = ['Yes', 'No']
CORS_OPTIONS = ['Yes', 'No', 'Unknown']

SELECTED_ENTRIES = [
    {
        "name": "AniAPI",
        "url": "https://aniapi.com/docs/",
        "line": 216,
        "category": "Anime",
        "raw": "| [AniAPI](https://aniapi.com/docs/) | Anime discovery, streaming & syncing with trackers | `OAuth` | Yes | Yes |"
    },
    {
        "name": "AniDB",
        "url": "https://wiki.anidb.net/HTTP_API_Definition",
        "line": 217,
        "category": "Anime",
        "raw": "| [AniDB](https://wiki.anidb.net/HTTP_API_Definition) | Anime Database | `apiKey` | No | Unknown |"
    },
    {
        "name": "AniList",
        "url": "https://github.com/AniList/ApiV2-GraphQL-Docs",
        "line": 218,
        "category": "Anime",
        "raw": "| [AniList](https://github.com/AniList/ApiV2-GraphQL-Docs) | Anime discovery & tracking | `OAuth` | Yes | Unknown |"
    }
]

def validate_section_format(lines: List[str], base_line_offset: int = 0) -> List[str]:
    """
    Validates Markdown table formatting, syntax, and alphabetical order in a section.
    Preserves non-English characters and valid markdown links.
    Returns list of error messages with source line numbers.
    """
    errors = []
    titles_in_order = []
    category_found = False

    for idx, raw_line in enumerate(lines):
        line_num = base_line_offset + idx + 1
        line = raw_line.rstrip('\r\n')
        
        if line.startswith('### '):
            category_found = True
            continue
            
        if not line.startswith('|') or line.startswith('|---') or line.startswith('|:---'):
            continue
            
        segments = line.split('|')[1:-1]
        if len(segments) != 5:
            errors.append(f"(L{line_num:03d}) Entry does not have all required 5 columns (got {len(segments)})")
            continue
            
        # Check segment spacing: must start and end with exactly 1 space
        for seg in segments:
            if len(seg) - len(seg.lstrip(' ')) != 1 or len(seg) - len(seg.rstrip(' ')) != 1:
                errors.append(f"(L{line_num:03d}) Each table segment must start and end with exactly 1 space")
                break
                
        cleaned_segments = [s.strip() for s in segments]
        title_seg, desc_seg, auth_seg, https_seg, cors_seg = cleaned_segments
        
        # Validate title
        m = LINK_RE.match(title_seg)
        if not m:
            errors.append(f"(L{line_num:03d}) Title syntax must be \"[TITLE](URL)\"")
            continue
            
        title = m.group(1)
        if title.upper().endswith(' API'):
            errors.append(f"(L{line_num:03d}) Title should not end with \"... API\". Every entry is an API here!")
            
        # Track title for alphabetical check (Unicode-aware uppercase sorting)
        titles_in_order.append((line_num, title, title.upper()))
        
        # Validate auth
        if auth_seg not in AUTH_OPTIONS:
            errors.append(f"(L{line_num:03d}) Invalid auth value: {auth_seg}")
            
        # Validate HTTPS
        if https_seg not in HTTPS_OPTIONS:
            errors.append(f"(L{line_num:03d}) Invalid HTTPS value: {https_seg}")
            
        # Validate CORS
        if cors_seg not in CORS_OPTIONS:
            errors.append(f"(L{line_num:03d}) Invalid CORS value: {cors_seg}")

    # Check alphabetical ordering
    for i in range(len(titles_in_order) - 1):
        curr_line, curr_title, curr_key = titles_in_order[i]
        next_line, next_title, next_key = titles_in_order[i + 1]
        if curr_key > next_key:
            errors.append(f"(L{next_line:03d}) Out of order: \"{next_title}\" must precede \"{curr_title}\" alphabetically")

    return errors

def get_fixtures() -> Dict[str, List[str]]:
    return {
        "valid_anime": [
            "### Anime",
            "API | Description | Auth | HTTPS | CORS |",
            "|:---|:---|:---|:---|:---|",
            "| [AniAPI](https://aniapi.com/docs/) | Anime discovery, streaming & syncing with trackers | `OAuth` | Yes | Yes |",
            "| [AniDB](https://wiki.anidb.net/HTTP_API_Definition) | Anime Database | `apiKey` | No | Unknown |",
            "| [AniList](https://github.com/AniList/ApiV2-GraphQL-Docs) | Anime discovery & tracking | `OAuth` | Yes | Unknown |"
        ],
        "valid_unicode": [
            "### Anime",
            "API | Description | Auth | HTTPS | CORS |",
            "|:---|:---|:---|:---|:---|",
            "| [AniList](https://github.com/AniList/ApiV2-GraphQL-Docs) | Anime discovery & tracking | `OAuth` | Yes | Unknown |",
            "| [Crunchyroll 日本語](https://crunchyroll.com/api) | Streaming catalog in Japanese | `apiKey` | Yes | Yes |"
        ],
        "malformed_out_of_order": [
            "### Anime",
            "API | Description | Auth | HTTPS | CORS |",
            "|:---|:---|:---|:---|:---|",
            "| [Z-Anime](https://z.example.com) | Alphabetically last | No | Yes | Yes |",
            "| [AniAPI](https://aniapi.com/docs/) | Out of order entry | `OAuth` | Yes | Yes |"
        ],
        "malformed_missing_column": [
            "### Anime",
            "API | Description | Auth | HTTPS | CORS |",
            "|:---|:---|:---|:---|:---|",
            "| [AniAPI](https://aniapi.com/docs/) | Missing last column | `OAuth` | Yes |"
        ],
        "malformed_ends_with_api": [
            "### Anime",
            "API | Description | Auth | HTTPS | CORS |",
            "|:---|:---|:---|:---|:---|",
            "| [AniDB API](https://wiki.anidb.net/HTTP_API_Definition) | Forbidden suffix | `apiKey` | No | Unknown |"
        ]
    }

def run_self_test() -> bool:
    print("[*] Running R02-T020 self-test on syntax and ordering fixtures...")
    fixtures = get_fixtures()

    # 1. Valid Anime section passes with zero errors
    errs_valid = validate_section_format(fixtures["valid_anime"], base_line_offset=213)
    assert len(errs_valid) == 0, f"Valid Anime section produced errors: {errs_valid}"
    print("  [PASS] Valid Anime catalogue section passed with zero errors")

    # 2. Non-English (Unicode) characters and markdown links are preserved
    errs_unicode = validate_section_format(fixtures["valid_unicode"], base_line_offset=100)
    assert len(errs_unicode) == 0, f"Valid Unicode entry produced errors: {errs_unicode}"
    print("  [PASS] Non-English text (日本語) and Markdown link syntax preserved")

    # 3. Out-of-order fixture rejected with source line
    errs_order = validate_section_format(fixtures["malformed_out_of_order"], base_line_offset=300)
    assert len(errs_order) > 0, "Out-of-order fixture unexpectedly passed"
    assert "(L305)" in errs_order[0] and "Out of order" in errs_order[0]
    print(f"  [PASS] Out-of-order fixture rejected with source line: {errs_order[0]}")

    # 4. Missing column rejected with source line
    errs_col = validate_section_format(fixtures["malformed_missing_column"], base_line_offset=400)
    assert len(errs_col) > 0, "Missing column fixture unexpectedly passed"
    assert "(L404)" in errs_col[0] and "5 columns" in errs_col[0]
    print(f"  [PASS] Missing column fixture rejected with source line: {errs_col[0]}")

    # 5. Title ending with " API" rejected with source line
    errs_api = validate_section_format(fixtures["malformed_ends_with_api"], base_line_offset=500)
    assert len(errs_api) > 0, "Title ending with ' API' unexpectedly passed"
    assert "(L504)" in errs_api[0] and "Title should not end with" in errs_api[0]
    print(f"  [PASS] Title ending with \"... API\" rejected with source line: {errs_api[0]}")

    print("[+] All R02-T020 self-test assertions PASSED successfully!")
    return True

def main():
    parser = argparse.ArgumentParser(description="R02-T020 Anime Formatting and Ordering Checker")
    parser.add_argument("--self-test", action="store_true", help="Run offline fixture verification assertions")
    parser.add_argument("--check-file", type=str, help="Validate an entire file or scoped section")
    args = parser.parse_args()

    if args.self_test:
        success = run_self_test()
        sys.exit(0 if success else 1)
        
    if args.check_file:
        with open(args.check_file, encoding='utf-8') as f:
            lines = f.readlines()
        errs = validate_section_format(lines)
        if errs:
            for e in errs:
                print(e)
            sys.exit(1)
        else:
            print("File format and ordering are valid.")
            sys.exit(0)

    run_self_test()

if __name__ == "__main__":
    main()
