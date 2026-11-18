# Course Checks

## R02-T044 — Verify entry metadata: Cryptocurrency [README.md]

### Purpose
Validates the table format, required fields, and metadata for the selected Cryptocurrency entries in `README.md`.

### Selected Entries
- [Coinlayer](https://coinlayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers) (line 501): `apiKey`, HTTPS: Yes, CORS: Unknown
- [0x](https://docs.0x.org/) (line 502): No, HTTPS: Yes, CORS: Yes
- [1inch](https://business.1inch.com/portal/documentation) (line 503): `apiKey`, HTTPS: Yes, CORS: Unknown

### Usage
From repository root:
```bash
python3 tools/course_checks/r02-t044.py
python3 tools/course_checks/r02-t044.py --self-test
```

### Fixtures
- `valid.md`: All 3 entries with correct metadata
- `missing-required-field.md`: Missing description
- `wrong-metadata.md`: Incorrect Auth, HTTPS, or CORS values
- `malformed-row.md`: Row with incomplete columns
