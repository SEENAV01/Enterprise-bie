"""Reproducible full repository ZIP backup from a verified committed Git tree."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
from pathlib import Path
import subprocess
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)

def main():
    p=argparse.ArgumentParser();p.add_argument("--output",type=Path,required=True);p.add_argument("--commit",default="HEAD");args=p.parse_args()
    sha=git("rev-parse",args.commit+"^{commit}").decode().strip()
    tree=git("rev-parse",sha+"^{tree}").decode().strip()
    archive=git("archive","--format=zip",sha)
    manifest={"schema_version":"1.0.0","repository":"https://github.com/SEENAV01/Enterprise-bie","commit_sha":sha,"tree_sha":tree,"accepted":False,"files":[]}
    args.output.parent.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(archive)) as source,zipfile.ZipFile(args.output,"w",zipfile.ZIP_DEFLATED,compresslevel=9) as target:
        for name in sorted(source.namelist()):
            if name.endswith("/"):continue
            data=source.read(name);info=zipfile.ZipInfo("my-book-intelligence-engine/"+name,(2026,9,9,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;target.writestr(info,data)
            manifest["files"].append({"path":name,"bytes":len(data),"sha256":hashlib.sha256(data).hexdigest()})
        info=zipfile.ZipInfo("BACKUP_MANIFEST.json",(2026,9,9,0,0,0));info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;target.writestr(info,json.dumps(manifest,indent=2,sort_keys=True)+"\n")
    with zipfile.ZipFile(args.output) as z:
        for item in manifest["files"]:
            if hashlib.sha256(z.read("my-book-intelligence-engine/"+item["path"])).hexdigest()!=item["sha256"]:raise SystemExit("Backup verification failed")
    print(json.dumps({"path":str(args.output.resolve()),"sha256":hashlib.sha256(args.output.read_bytes()).hexdigest(),"file_count":len(manifest["files"]),"commit_sha":sha,"tree_sha":tree,"verified":True}))

if __name__=="__main__":main()
