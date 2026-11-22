# R02-T051 Manual Verification

> **Status: NOT YET OBSERVED** — The automated checker ran inside a network-sandboxed
> environment and could not reach the target URLs. Run the commands below to collect
> live evidence.

## Target Entries

| Entry | README Line | Original URL |
|-------|-------------|--------------|
| Currencylayer | L609 | https://currencylayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| Exchangerate.host | L610 | https://exchangerate.host?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |
| Exchangeratesapi.io | L611 | https://exchangeratesapi.io?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers |

## Observation Table (Fill In After Running Commands)

| Entry | Original URL | Final Official URL | Observation Date | Classification | Notes |
|-------|-------------|-------------------|-----------------|----------------|-------|
| Currencylayer | https://currencylayer.com | NOT YET OBSERVED | — | — | utm_flagged |
| Exchangerate.host | https://exchangerate.host | NOT YET OBSERVED | — | — | utm_flagged; keyless access ended 2023 per README |
| Exchangeratesapi.io | https://exchangeratesapi.io | NOT YET OBSERVED | — | — | utm_flagged |

## Commands to Run

### 1. curl — trace the full redirect chain (run once per entry)

```bash
# Currencylayer
curl -sI -L --max-redirs 5 --max-time 10 \
  "https://currencylayer.com?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers" \
  | grep -E "^(HTTP|Location|location):"

# Exchangerate.host
curl -sI -L --max-redirs 5 --max-time 10 \
  "https://exchangerate.host?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers" \
  | grep -E "^(HTTP|Location|location):"

# Exchangeratesapi.io
curl -sI -L --max-redirs 5 --max-time 10 \
  "https://exchangeratesapi.io?utm_source=Github&utm_medium=Referral&utm_campaign=Public-apis-repo-Best-sellers" \
  | grep -E "^(HTTP|Location|location):"
```

### 2. Python checker — live mode (writes work/R02-T051/report.json)

```bash
python3 tools/course_checks/r02-t051.py --live
```

### 3. Self-test (must always exit 0 on a clean repo)

```bash
python3 tools/course_checks/r02-t051.py --self-test
echo "Exit: $?"
```

## After Running

1. Fill in the observation table above with the results.
2. If `classification == moved_permanent` and `final_url` differs from the original,
   update `report.json` with the live results.
3. Only correct the README entry if **all** of the following hold:
   - The redirect is permanent (301 or 308), not temporary.
   - The final URL returns 200 (not a login wall or error).
   - You have confirmed the final URL is the official API page manually.
   - The utm_* parameters are **not** carried into the corrected URL
     (strip them only after manual confirmation the destination is correct).
4. If in doubt, leave the entry unchanged and add a note here.
