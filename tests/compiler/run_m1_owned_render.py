"""M1 test-only root supervisor, following the canonical native-render boundary.

Copies exact tracked sources into a private root-owned engine. Never changes
checkout permissions; no worker/kernel policy or compiler limit is relaxed.
Only bounded allowlisted JSON escapes the private engine. Not product execution.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from tests.compiler.run_motion_m1 import safe_error


def require(value, code):
    if not value: raise ValueError("M1_SUPERVISOR_" + code)


def main():
    p=argparse.ArgumentParser()
    p.add_argument("--family",choices=("quantitative","chronology","cellular","cellular_reduced"),required=True)
    p.add_argument("--preference",choices=("standard","reduced"),required=True)
    p.add_argument("--output",type=Path,required=True)
    args=p.parse_args()
    result={"schema":"bie.task036.m1-owned-render/1","passed":False,"native_test_only":True,
        "original_checkout_permissions_changed":False,"product_accepted":False}
    try:
        require(sys.platform=="linux" and os.getuid()==0,"ROOT_LINUX_REQUIRED")
        require(not args.output.exists() and not args.output.is_symlink(),"OUTPUT_EXISTS")
        with tempfile.TemporaryDirectory(prefix="bie-m1-owned-native-") as tmp:
            private=Path(tmp); source=private/"source"; source.mkdir()
            names=subprocess.check_output(["git","-c","safe.directory="+str(ROOT),"ls-files","-z"],cwd=ROOT).split(b"\0")
            hashes={}; total=0
            for raw in names:
                if not raw: continue
                rel=Path(raw.decode("utf-8"))
                if rel.parts[0] not in ("bie","apps","tests","docs","tools","task_registry","fixtures"):continue
                if rel.suffix.lower() not in (".py",".json",".js",".cjs",".ts",".tsx",".html",".css",".md",".txt"):continue
                path=ROOT/rel
                require(path.is_file() and not path.is_symlink() and path.stat().st_size<=16*1024**2,"SOURCE_FILE")
                data=path.read_bytes();total+=len(data)
                require(total<=256*1024**2 and len(hashes)<15000,"SOURCE_BUDGET")
                dest=source/rel;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(data)
                h=hashlib.sha256(data).hexdigest()
                require(hashlib.sha256(dest.read_bytes()).hexdigest()==h,"COPY_IDENTITY")
                hashes[rel.as_posix()]=h
            env={"PATH":"/usr/local/libexec/bie-integration:/opt/nvm/versions/node/v22.16.0/bin:/opt/pyvenv/bin:/usr/local/bin:/usr/bin:/bin",
                "LANG":"C.UTF-8","HOME":str(private),"PYTHONDONTWRITEBYTECODE":"1","PYTHONUTF8":"1"}
            out=private/"receipt.json"
            command=[sys.executable,"-I","-B",str(source/"tests/compiler/run_motion_m1.py"),"--mode","render",
                "--family",args.family,"--preference",args.preference,"--browser","/usr/local/lib/bie-section18-chromium/chrome","--output",str(out)]
            completed=subprocess.run(command,cwd=source,env=env,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=600)
            require(len(completed.stdout)+len(completed.stderr)<=2*1024**2,"OUTPUT_BUDGET")
            require(out.is_file() and out.stat().st_size<=128*1024,"RECEIPT_REQUIRED")
            receipt=json.loads(out.read_text(encoding="utf-8"))
            # This child authors only the fixed safe receipt in run_motion_m1.
            # No raw child stdout/stderr, project, source, media or font is copied.
            result["proof"]=receipt
            require(completed.returncode==0 and receipt.get("passed") is True,"CHILD_GATE")
            require(all(hashlib.sha256((source/k).read_bytes()).hexdigest()==h for k,h in hashes.items()),"ENGINE_CHANGED")
            require(all(hashlib.sha256((ROOT/k).read_bytes()).hexdigest()==h for k,h in hashes.items()),"CHECKOUT_CHANGED")
            result.update(passed=True,source_files=len(hashes),source_bytes=total,
                source_inventory_sha256=hashlib.sha256(json.dumps(hashes,sort_keys=True).encode()).hexdigest(),
                source_bytes_unchanged=True)
    except Exception as exc: result["failure"]=safe_error(exc)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({"passed":result["passed"],"failure":result.get("failure"),"product_accepted":False}))
    return 0 if result["passed"] else 1


if __name__=="__main__":raise SystemExit(main())
