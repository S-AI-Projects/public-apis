#!/usr/bin/env python3
"""Validate the Sports & Fitness table and emit source-line evidence (offline)."""
import argparse, json, re, sys
from pathlib import Path
SECTION = "Sports & Fitness"
TARGETS = {"5DollarFootball", "AcesAPI", "API-FOOTBALL"}
AUTH = {"OAuth", "apiKey", "X-Mashape-Key", "No", "User-Agent"}
CORS = {"Yes", "No", "Unknown"}

def parse(text):
    rows, active = [], False
    for line_no, line in enumerate(text.splitlines(), 1):
        if line.strip() == "### " + SECTION: active = True; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        cells = [x.strip() for x in line.strip().strip("|").split("|")]
        if cells and cells[0].lower() == "api": continue
        if len(cells) != 5:
            rows.append({"line": line_no, "valid": False, "errors": ["expected exactly 5 columns"]}); continue
        m = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)", cells[0])
        errors = []
        if not m: errors.append("API cell must be a Markdown link with an HTTP(S) URL")
        if not cells[1]: errors.append("description is required")
        if len(cells[1]) > 100: errors.append("description exceeds 100 characters")
        auth = cells[2].strip("`")
        if auth not in AUTH: errors.append("unsupported Auth value")
        if cells[3] not in {"Yes", "No"}: errors.append("HTTPS must be Yes or No")
        if cells[4] not in CORS: errors.append("CORS must be Yes, No or Unknown")
        row = {"line": line_no, "valid": not errors, "errors": errors}
        if m: row.update(name=m.group(1), url=m.group(2))
        row.update(description=cells[1], auth=auth, https=cells[3], cors=cells[4])
        rows.append(row)
    return rows

def self_test():
    fixture = """### Sports & Fitness
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [5DollarFootball](https://5dollarfootballapi.com/) | Fixtures | apiKey | Yes | Yes |
| [AcesAPI](https://acesapi.com/docs) | Tennis | apiKey | Yes | Yes |
| [API-FOOTBALL](https://www.api-football.com/documentation-v3) | Football | apiKey | Yes | Yes |
| [Broken](https://example.com) |  | apiKey | Yes | Yes |
"""
    got = parse(fixture)
    valid = [r for r in got if r["valid"]]
    invalid = [r for r in got if not r["valid"]]
    assert [r["name"] for r in valid] == ["5DollarFootball", "AcesAPI", "API-FOOTBALL"]
    assert len(invalid) == 1 and invalid[0]["line"] == 7 and "description is required" in invalid[0]["errors"]
    assert all(r["line"] == i for r, i in zip(got, [4,5,6,7]))
    return {"passed": 3, "valid_rows": len(valid), "rejected_rows": invalid}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        rows=parse(Path(a.readme).read_text(encoding="utf-8"))
        selected=[r for r in rows if r.get("name") in TARGETS]
        evidence=[{"entry":r["name"],"source_url":r["url"],"source_line":r["line"],"observed_value":{k:r[k] for k in ("description","auth","https","cors")},"proposed_value":{k:r[k] for k in ("description","auth","https","cors")},"change":"none; no verified correction proposed","valid":r["valid"],"errors":r["errors"]} for r in selected]
        result={"section":SECTION,"entries":evidence,"missing_targets":sorted(TARGETS-{r["entry"] for r in evidence})}
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
