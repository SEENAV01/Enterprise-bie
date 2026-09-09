"""Fast-forward Git synchronization for an authenticated ordinary checkout.

The first synchronization performs a real remote probe commit on a temporary
branch before pushing the already validated mainline commit. No force pushes.
Connector-only sessions use the equivalent Git Data API sequence in the guide.
"""
from pathlib import Path
import argparse
import json
import subprocess
import sys
import tempfile
import uuid

ROOT=Path(__file__).resolve().parents[1]
EXPECTED="SEENAV01/Enterprise-bie"

def git(*args,check=True,input=None):
    r=subprocess.run(["git",*args],cwd=ROOT,text=True,input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
    if check and r.returncode:raise RuntimeError("Git operation failed: "+" ".join(args[:2])+"; check local Git authentication and branch policy")
    return r

def main():
    parser=argparse.ArgumentParser();parser.add_argument("--branch",default="main");args=parser.parse_args()
    branch=args.branch
    if git("check-ref-format","--branch",branch,check=False).returncode:raise SystemExit("Invalid branch")
    remote=git("remote","get-url","origin").stdout.strip().removesuffix(".git")
    if remote not in {"https://github.com/"+EXPECTED,"git@github.com:"+EXPECTED}:raise SystemExit("Unexpected origin repository")
    if git("status","--porcelain").stdout.strip():raise SystemExit("Commit intended changes and preserve all other working changes before synchronizing")
    with tempfile.TemporaryDirectory(prefix="bie-sync-check-") as output:
        subprocess.run([sys.executable,str(ROOT/"scripts/integrated_check.py"),"--output-dir",output],cwd=ROOT,check=True)
    git("fetch","origin",branch)
    base=git("rev-parse","FETCH_HEAD").stdout.strip();head=git("rev-parse","HEAD").stdout.strip()
    if git("merge-base","--is-ancestor",base,head,check=False).returncode:raise SystemExit("Remote diverged; integrate remote changes before retrying")
    # A real tiny probe commit uses the same tree and preserves branch history.
    tree=git("rev-parse",base+"^{tree}").stdout.strip()
    probe=git("commit-tree",tree,"-p",base,input="chore: verify BIE synchronization write capability\n").stdout.strip()
    probe_branch="bie-write-probe-"+uuid.uuid4().hex[:12]
    git("push","origin",probe+":refs/heads/"+probe_branch)
    readback=git("ls-remote","origin","refs/heads/"+probe_branch).stdout.split()
    if not readback or readback[0]!=probe:raise SystemExit("Probe readback mismatch; main branch not pushed")
    git("push","origin",head+":refs/heads/"+branch)
    actual=git("ls-remote","origin","refs/heads/"+branch).stdout.split()
    if not actual or actual[0]!=head:raise SystemExit("Remote commit verification failed")
    # Retain the probe branch as write evidence. It contains no alternate code.
    print(json.dumps({"repository":EXPECTED,"branch":branch,"commit_sha":head,"probe_commit_sha":probe,"probe_branch":probe_branch,"verified":True}))

if __name__=="__main__":main()
