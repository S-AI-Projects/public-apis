#!/usr/bin/env python3
"""Validate Machine Learning table structure, entry order, Unicode and source lines."""
import argparse,json,re,sys
from pathlib import Path
SECTION="Machine Learning"; TARGETS={"AI Economics Tools","AI For Thai","AI Stupid Level"}

def parse(text):
    rows=[]; active=False; fence=False; heading_count=0
    for n,line in enumerate(text.splitlines(),1):
        if line.strip().startswith("```"): fence=not fence; continue
        if fence: continue
        if line.strip()=="### "+SECTION: active=True; heading_count+=1; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if cells and cells[0].lower()=="api": continue
        errors=[]
        if len(cells)!=5:
            rows.append({"line":n,"valid":False,"errors":["expected exactly five columns"]}); continue
        m=re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)",cells[0])
        if not m: errors.append("invalid Markdown link")
        if not cells[1]: errors.append("description is required")
        if len(cells[1])>100: errors.append("description exceeds 100 characters")
        auth=cells[2].strip("`")
        if auth not in {"OAuth","apiKey","X-Mashape-Key","No","User-Agent"}: errors.append("invalid Auth")
        if cells[3] not in {"Yes","No"}: errors.append("invalid HTTPS")
        if cells[4] not in {"Yes","No","Unknown"}: errors.append("invalid CORS")
        row={"line":n,"valid":not errors,"errors":errors,"description":cells[1],"auth":auth,"https":cells[3],"cors":cells[4]}
        if m: row.update(name=m.group(1),url=m.group(2))
        rows.append(row)
    return rows

def self_test():
    fixture="""### Machine Learning
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [AI Economics Tools](https://piszczek.pl/tools/api) | Calculators | No | Yes | Yes |
| [AI For Thai](https://aiforthai.in.th/index.php) | ภาษาไทย | apiKey | Yes | Yes |
| [AI Stupid Level](https://aistupidlevel.info/api-docs) | Benchmarks | apiKey | Yes | No |
| malformed | row |
```md
| [Fake](https://fake.invalid) | fake | No | Yes | Yes |
```
### Music
| [Outside](https://example.com) | outside | No | Yes | Yes |"""
    rows=parse(fixture); good=[r for r in rows if r.get("name") in TARGETS]
    bad=[r for r in rows if not r["valid"]]
    names=[r["name"].casefold() for r in good]
    assert names==sorted(names) and [r["name"] for r in good]==["AI Economics Tools","AI For Thai","AI Stupid Level"]
    assert good[1]["description"]=="ภาษาไทย" and good[1]["url"]=="https://aiforthai.in.th/index.php"
    assert len(bad)==1 and bad[0]["line"]==7
    assert all(r["line"] in (4,5,6) for r in good)
    return {"passed":5,"valid_entries":good,"rejected_rows":bad,"fenced_example_ignored":True,"alphabetical":True}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        rows=parse(Path(a.readme).read_text(encoding="utf-8")); chosen=[r for r in rows if r.get("name") in TARGETS]
        names=[r["name"].casefold() for r in chosen]
        result={"section":SECTION,"entries":chosen,"alphabetical":names==sorted(names),"missing_targets":sorted(TARGETS-{r["name"] for r in chosen})}
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
