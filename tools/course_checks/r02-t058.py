#!/usr/bin/env python3
"""Report evidence-backed access requirements for three Dictionaries entries."""
import argparse,json,re,sys
from pathlib import Path
TARGETS={"Chinese Character Web","Chinese Text Project","Collins"}
SOURCES={
 "Chinese Character Web":{"official":"http://ccdb.hemiola.com/","finding":"unverified","auth":"unverified","registration":"unverified","payment":"unverified","environment":"unverified","basis":"No authoritative API access documentation was located; do not infer that it is free or broken."},
 "Chinese Text Project":{"official":"https://ctext.org/tools/api","subscription":"https://ctext.org/tools/subscribe","finding":"tiered access","auth":"No for limited unauthenticated use; API key/login or institutional access is required for additional authenticated functions","registration":"CTP account for higher user tier; institutional access via subscription","payment":"Basic unauthenticated access is limited; institutional subscription provides extended access","environment":"Client-side JavaScript/CORS is supported; institution-registered IPs provide subscriber access","basis":"Official API documentation says all users may use the API with group-based rate limits; some functions return authentication-required errors. Subscription page describes API keys and institutional access."},
 "Collins":{"official":"https://www.collinsdictionary.com/collins-api","terms":"https://blog.collinsdictionary.com/terms-conditions-collins-api/","key_form":"https://blog.collinsdictionary.com/collins-api-apply-for-a-key/","finding":"API key and registration required","auth":"apiKey","registration":"Apply for a separate API key and register for each use","payment":"Non-commercial use currently free; English-only and bilingual APIs list up to 5,000 calls/month free. Commercial use requires a paid licence","environment":"unverified","basis":"Official Collins API page publishes tiers; official terms require registration/key and distinguish non-commercial and commercial licences."}
}

def parse(text):
    rows=[]; active=False
    for n,line in enumerate(text.splitlines(),1):
        if line.strip()=="### Dictionaries": active=True; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        c=[x.strip() for x in line.strip().strip("|").split("|")]
        if c and c[0].lower()=="api": continue
        if len(c)!=5: continue
        m=re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)",c[0])
        if m and m.group(1) in TARGETS:
            rows.append({"line":n,"name":m.group(1),"url":m.group(2),"description":c[1],"catalogue_auth":c[2].strip("`"),"https":c[3],"cors":c[4]})
    return rows

def build_report(text):
    rows=parse(text); result=[]
    for row in rows:
        finding=SOURCES[row["name"]]
        result.append({"source_line":row["line"],"name":row["name"],"catalogue_observed":row,"access_assessment":finding})
    return {"section":"Dictionaries","entries":result,"missing_targets":sorted(TARGETS-{r["name"] for r in rows}),"credentials_stored":False}

def self_test():
    fixture="""### Dictionaries
| API | Description | Auth | HTTPS | CORS |
|:---|:---|:---|:---|:---|
| [Chinese Character Web](http://ccdb.hemiola.com/) | Chinese characters | No | No | No |
| [Chinese Text Project](https://ctext.org/tools/api) | Chinese texts | No | Yes | Unknown |
| [Collins](https://api.collinsdictionary.com/api/v1/documentation/html/) | Dictionaries | apiKey | Yes | Unknown |"""
    r=build_report(fixture); e={x["name"]:x for x in r["entries"]}
    assert len(e)==3 and e["Chinese Character Web"]["access_assessment"]["finding"]=="unverified"
    assert "limited" in e["Chinese Text Project"]["access_assessment"]["auth"]
    assert e["Collins"]["access_assessment"]["auth"]=="apiKey"
    assert e["Collins"]["access_assessment"]["registration"].startswith("Apply")
    assert not r["credentials_stored"]
    assert [x["source_line"] for x in r["entries"]]==[4,5,6]
    return {"passed":5,"report":r,"network_used":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        result=build_report(Path(a.readme).read_text(encoding="utf-8")); s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
