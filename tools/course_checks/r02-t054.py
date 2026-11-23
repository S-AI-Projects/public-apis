#!/usr/bin/env python3
"""Classify probe outcomes and report selected Art & Design rows with source lines."""
import argparse,json,sys
from pathlib import Path
TARGETS={"3DTexel","Améthyste","Art Institute of Chicago"}

def classify(status=None,error=None,method="GET",fallback_status=None,confirmed_missing=False):
    if error=="timeout": return "timeout"
    if error in {"dns","gaierror"}: return "dns_failure"
    if error: return "network_error"
    if status==405 and method.upper()=="HEAD":
        return classify(fallback_status) if fallback_status is not None else "head_unsupported"
    if status in (403,429): return "forbidden_or_rate_limited"
    if status==404: return "confirmed_missing" if confirmed_missing else "missing_unconfirmed"
    if status is not None and 200<=status<400: return "success"
    return "http_error" if status is not None else "unknown"

def parse_section(text):
    rows=[]; active=False
    for n,line in enumerate(text.splitlines(),1):
        if line.strip()=="### Art & Design": active=True; continue
        if active and line.startswith("### "): break
        if not active or not line.lstrip().startswith("|") or line.lstrip().startswith("|:"): continue
        cells=[x.strip() for x in line.strip().strip("|").split("|")]
        if cells and cells[0].lower()=="api": continue
        if len(cells)!=5 or not cells[0].startswith("["): continue
        import re
        m=re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)",cells[0])
        if m and m.group(1) in TARGETS:
            rows.append({"line":n,"name":m.group(1),"url":m.group(2),"description":cells[1],"auth":cells[2].strip("`"),"https":cells[3],"cors":cells[4]})
    return rows

def self_test():
    cases=[
      ({"status":200},"success"),
      ({"status":404},"missing_unconfirmed"),
      ({"status":404,"confirmed_missing":True},"confirmed_missing"),
      ({"status":429},"forbidden_or_rate_limited"),
      ({"status":403},"forbidden_or_rate_limited"),
      ({"status":405,"method":"HEAD","fallback_status":200},"success"),
      ({"error":"timeout"},"timeout"),
      ({"error":"dns"},"dns_failure")]
    results=[{"input":x,"expected":y,"actual":classify(**x)} for x,y in cases]
    assert all(x["actual"]==x["expected"] for x in results)
    fixture="### Art & Design\n| API | Description | Auth | HTTPS | CORS |\n|:---|:---|:---|:---|:---|\n| [3DTexel](https://3dtexel.com/developers/#public-api) | 3D | No | Yes | Yes |\n| [Améthyste](https://api.amethyste.moe/) | Images | apiKey | Yes | Unknown |\n| [Art Institute of Chicago](https://api.artic.edu/docs/) | Art | No | Yes | Yes |\n### Animals\n| [Not in scope](https://example.com) | x | No | Yes | Yes |"
    rows=parse_section(fixture)
    assert [r["name"] for r in rows]==["3DTexel","Améthyste","Art Institute of Chicago"]
    assert [r["line"] for r in rows]==[4,5,6]
    return {"passed":10,"classification_cases":results,"fixture_rows":rows,"network_used":False}

def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(self_test(),ensure_ascii=False,indent=2)); return 0
    if a.report:
        rows=parse_section(Path(a.readme).read_text(encoding="utf-8"))
        result={"section":"Art & Design","entries":rows,"missing_targets":sorted(TARGETS-{r["name"] for r in rows}),"policy":"A single automated failure never recommends removal; 404 requires independent manual confirmation."}
        s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
