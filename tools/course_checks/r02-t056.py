#!/usr/bin/env python3
"""Offline parser/validator for selected Finance catalogue rows."""
import argparse,json,re,sys
from pathlib import Path
SECTION="Finance"; TARGETS={"Marketstack","Aletheia","Alpaca"}

def parse(text):
    rows=[]; active=False
    for n,line in enumerate(text.splitlines(),1):
        if line.strip()=="### "+SECTION: active=True; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if cells and cells[0].lower()=="api": continue
        if len(cells)==5 and all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells): continue
        if len(cells)!=5:
            rows.append({"line":n,"valid":False,"errors":["expected exactly five columns"]}); continue
        m=re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)",cells[0])
        errors=[]
        if not m: errors.append("invalid Markdown API link")
        if not cells[1]: errors.append("description is required")
        if len(cells[1])>100: errors.append("description exceeds 100 characters")
        auth=cells[2].strip("`")
        if auth not in {"OAuth","apiKey","X-Mashape-Key","No","User-Agent"}: errors.append("invalid Auth value")
        if cells[3] not in {"Yes","No"}: errors.append("invalid HTTPS value")
        if cells[4] not in {"Yes","No","Unknown"}: errors.append("invalid CORS value")
        row={"line":n,"valid":not errors,"errors":errors,"description":cells[1],"auth":auth,"https":cells[3],"cors":cells[4]}
        if m: row.update(name=m.group(1),url=m.group(2))
        rows.append(row)
    return rows

def self_test():
    fixture="""### Finance
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [Marketstack](https://marketstack.com/?a=1&b=x%2Fy) | Quotes | apiKey | Yes | Unknown |
| [Aletheia](https://aletheiaapi.com/) | Finance | apiKey | Yes | Yes |
| [Alpaca](https://docs.alpaca.markets/us/docs/about-market-data-api) | Stocks | apiKey | Yes | Yes |
| [Broken](https://example.com) |  | apiKey | Yes | Yes |
### Food
| [Out of scope](https://example.com) | no | No | Yes | Yes |"""
    rows=parse(fixture); selected=[r for r in rows if r.get("name") in TARGETS]
    assert [r["name"] for r in selected]==["Marketstack","Aletheia","Alpaca"]
    assert selected[0]["url"].endswith("b=x%2Fy")
    bad=[r for r in rows if not r["valid"]]
    assert len(bad)==1 and bad[0]["line"]==7 and "description is required" in bad[0]["errors"]
    assert all(r["line"] in (4,5,6) for r in selected)
    return {"passed":4,"selected_rows":selected,"rejected_rows":bad,"network_used":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        rows=parse(Path(a.readme).read_text(encoding="utf-8")); selected=[r for r in rows if r.get("name") in TARGETS]
        missing=sorted(TARGETS-{r["name"] for r in selected})
        invalid=[r for r in selected if not r["valid"]]
        result={"section":SECTION,"entries":selected,"missing_targets":missing,"invalid_entries":invalid,"network_used":False}
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end="")
        return 1 if missing or invalid else 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
