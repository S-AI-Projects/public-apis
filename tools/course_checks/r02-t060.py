#!/usr/bin/env python3
"""Create a stable, source-line-aware maintenance report for Anime catalogue rows."""
import argparse,json,re,sys
from pathlib import Path
TARGETS={"AniAPI","AniDB","AniList"}
def collect(readme):
    lines=Path(readme).read_text(encoding="utf-8").splitlines()
    start=next((i for i,x in enumerate(lines) if x.strip()=="### Anime"),None)
    if start is None: raise ValueError("Anime section not found")
    entries=[]
    for i,line in enumerate(lines[start+1:],start+2):
        if line.startswith("### "): break
        m=re.match(r"^\|\s*\[([^\]]+)\]\(([^)]+)\)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|?$",line)
        if not m or m.group(1) not in TARGETS: continue
        observed={"description":m.group(3),"auth":m.group(4),"https":m.group(5),"cors":m.group(6)}
        entries.append({"line":i,"name":m.group(1),"url":m.group(2),"before":observed,"after":observed.copy(),"manual_decision":"No change; no new official-source evidence was established by this offline report.","recommendation":"Retain until any proposed correction is verified against the official source."})
    return {"section":"Anime","entries":entries,"source_lines":[e["line"] for e in entries],"stable_output":True}
def test():
    fixture="### Anime\nAPI | Description | Auth | HTTPS | CORS |\n|:---|:---|:---|:---|:---|\n| [AniAPI](https://aniapi.com/docs/) | Anime | OAuth | Yes | Yes |\n| [AniDB](https://wiki.anidb.net/HTTP_API_Definition) | Database | apiKey | No | Unknown |\n| [AniList](https://github.com/AniList/ApiV2-GraphQL-Docs) | Tracking | OAuth | Yes | Unknown |"
    import tempfile
    with tempfile.NamedTemporaryFile("w",encoding="utf-8",delete=False) as f: f.write(fixture); name=f.name
    try:
        one=collect(name); two=collect(name)
        assert one==two and len(one["entries"])==3
        assert one["source_lines"]==[4,5,6]
        assert all("before" in e and "after" in e and "manual_decision" in e for e in one["entries"])
    finally: Path(name).unlink(missing_ok=True)
    return {"passed":3,"entries":["AniAPI","AniDB","AniList"],"repeat_output_identical":True,"before_after_metadata_included":True}
def main():
    p=argparse.ArgumentParser(); p.add_argument("--self-test",action="store_true"); p.add_argument("--report",action="store_true"); p.add_argument("--readme",default="README.md"); p.add_argument("--output"); a=p.parse_args()
    if a.self_test: print(json.dumps(test(),indent=2)); return 0
    if a.report:
        result=collect(a.readme); s=json.dumps(result,ensure_ascii=False,indent=2)+"\n"
        if a.output: Path(a.output).write_text(s,encoding="utf-8")
        print(s,end=""); return 0
    p.error("choose --self-test or --report")
if __name__=="__main__": sys.exit(main())
