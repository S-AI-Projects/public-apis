# Course Check R02-T052: Duplicate URL Checker

Automated duplicate-URL detection tool with conservative normalization and strict safety guardrails for the `public-apis` repository.

## Selected Entries for Task R02-T052

The checker focuses on the following three entries located under `### Anti-Malware` in `README.md`:

| Line | Entry Name | URL in README | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|:---|
| 244 | **AbuseIPDB** | `https://docs.abuseipdb.com/` | `apiKey` | Yes | Unknown |
| 245 | **AlienVault Open Threat Exchange (OTX)** | `https://otx.alienvault.com/api` | `apiKey` | Yes | Unknown |
| 246 | **CAPEsandbox** | `https://capev2.readthedocs.io/en/latest/usage/api.html` | `apiKey` | Yes | Unknown |

---

## Normalization Specification

### 1. Conservative Normalization Rules
The checker only collapses URLs that match under conservative, unambiguous normalization rules:
- **Scheme & Host Case**: Schemes (`http`, `https`) and hostnames/domains are lowercased (e.g. `https://DOCS.ABUSEIPDB.COM/` -> `https://docs.abuseipdb.com`).
- **Default Ports**: Default port specifications are stripped (`:80` for `http`, `:443` for `https`). Non-default ports (e.g. `:8080`, `:8443`) are strictly preserved.
- **Trailing Slashes**: Trailing slashes on paths are stripped (e.g. `https://otx.alienvault.com/api/` -> `https://otx.alienvault.com/api`).
- **Bare Host vs Root Path**: A bare host without a path (`https://example.com`) and a root path (`https://example.com/`) normalize identically to `https://example.com`.

Nothing more aggressive is performed.

### 2. Kept Distinct Rules
The following URLs are strictly **kept distinct** and never grouped as duplicates:
- **Query Strings**: URLs differing in query string parameters are query-dependent resources and must not be collapsed (e.g. `?mode=simple` vs `?mode=extended`).
- **Campaign / UTM Parameters**: Query parameters such as `utm_source`, `utm_medium`, etc., are **not** auto-stripped and are kept distinct.
- **Fragments / Anchors**: URLs with distinct fragments (e.g. `#overview` vs `#endpoints`) point to distinct sub-resources or sections.
- **Path Casing**: Path casing is strictly case-sensitive according to RFC standards (e.g. `/api` vs `/API`).
- **Protocols (HTTP vs HTTPS)**: Plaintext `http://` and encrypted `https://` remain distinct resources.

---

## Review-Pair Format & Proposed Deletions

The checker enforces strict safety rules:
- **No Automatic Edits**: The checker **never** modifies or deletes entries in `README.md` automatically.
- **Reviewed-Pair Requirement**: A proposed deletion is allowed only as a human-vetted recommendation and **must** be accompanied by a manually reviewed pair entry with an explicit decision.
- **Validation**: If any proposed deletion is supplied without a matching reviewed pair, or if the reviewer decision is missing/ambiguous (`manual_review`), the checker rejects the operation with a non-zero exit code.

### Reviewed Pair JSON Schema
```json
[
  {
    "entry_keep": {
      "name": "AbuseIPDB",
      "url": "https://docs.abuseipdb.com/",
      "line": 244
    },
    "entry_remove": {
      "name": "AbuseIPDB Duplicate",
      "url": "https://docs.abuseipdb.com",
      "line": 999
    },
    "duplicate_type": "normalized",
    "normalization_reasons": ["trailing_slash"],
    "reviewer": "divyanshiyadav396-lab",
    "decision": "keep_first",
    "rationale": "Entry at line 244 is the canonical entry; line 999 is a trailing-slash duplicate."
  }
]
```

---

## Usage

### 1. Run Self-Test Suite
Executes all 10 offline JSON fixtures in `tools/course_checks/fixtures/r02-t052/` and runs an internal negative test ensuring failure exit codes on erroneous expectations:
```bash
python3 tools/course_checks/r02-t052.py --self-test
```
Exits `0` on success and non-zero on failure.

### 2. Check Specific Section in README.md
Analyze entries in the `Anti-Malware` section:
```bash
python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware
```

### 3. Check Selected Entries Only
Filter analysis strictly to the 3 selected entries:
```bash
python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware --selected-only
```

### 4. Output Machine-Readable JSON
```bash
python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware --selected-only --json
```

### 5. Validate Proposed Deletions Against Reviewed Pairs
```bash
python3 tools/course_checks/r02-t052.py --proposed-deletions deletions.json --reviewed-pairs pairs.json
```

### 6. Optional Bounded Live Check
```bash
python3 tools/course_checks/r02-t052.py --readme README.md --section Anti-Malware --selected-only --live-check
```
Enforces sequential execution, 5.0s timeout per request, at most 5 hops, a polite User-Agent, and capped requests. Live results are optional support evidence only.
