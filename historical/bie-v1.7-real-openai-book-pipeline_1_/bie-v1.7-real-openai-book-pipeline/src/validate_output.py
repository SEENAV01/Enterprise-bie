import json,sys
from pathlib import Path
u=json.loads(Path(sys.argv[1]).read_text()); errors=[]
if not u.get("source_refs"): errors.append("missing source_refs")
if not 0<=u.get("confidence",-1)<=1: errors.append("bad confidence")
for c in u.get("claims",[]):
    if not c.get("evidence_refs"): errors.append(c.get("claim_id","claim")+" missing evidence")
print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},indent=2))
raise SystemExit(bool(errors))
