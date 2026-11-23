#!/usr/bin/env python3
"""Extract structured Tracking entries, metadata and original README line numbers."""
import argparse,json,re,sys
from pathlib import Path
TARGETS={"Aftership","Correios","Mapbox"}; CATEGORY="Tracking"

def parse(text):
    rows=[]; active=False; fence=False
    for n,line in enumerate(text.splitlines(),1):
        if line.strip().startswith("```"): fence=not fence; continue
        if fence: continue
        if line.strip()=="### "+CATEGORY: active=True; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if cells and cells[0].lower()=="api": continue
        if len(cells)!=5: continue
        m=re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)",cells[0])
        if not m or m.group(1) not in TARGETS: continue
        rows.append({"source_line":n,"display_name":m.group(1),"url":m.group(2),"category":CATEGORY,"description":cells[1],"auth":cells[2].strip("`"),"https":cells[3],"cors":cells[4]})
    return rows

def self_test():
    fixture="""### Tracking
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
```md
| [Fake](https://fake.invalid) | fake | No | Yes | Yes |
```
| [Aftership](https://developers.aftership.com/reference/quick-start) | Tracking | apiKey | Yes | Yes |
| [Correios](https://cws.correios.com.br/ajuda) | Correios | apiKey | Yes | Unknown |
| [Mapbox](https://docs.mapbox.com/api/#directions) | Maps | apiKey | Yes | Unknown |
### Other
| [Ignored](https://example.com) | ignored | No | Yes | Yes |"""
    rows=parse(fixture)
    assert [r["display_name"] for r in rows]==["Aftership","Correios","Mapbox"]
    assert [r["source_line"] for r in rows]==[7,8,9]
    assert rows[-1]["url"]=="https://docs.mapbox.com/api/#directions"
    assert all(r["category"]==CATEGORY and r["description"] and r["auth"] for r in rows)
    return {"passed":4,"entries":rows,"fenced_fake_ignored":True,"fragment_preserved":True,"network_used":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        rows=parse(Path(a.readme).read_text(encoding="utf-8")); result={"category":CATEGORY,"entries":rows,"missing_targets":sorted(TARGETS-{r["display_name"] for r in rows})}
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
