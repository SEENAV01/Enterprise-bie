import json, sys
from pathlib import Path

CRITICAL={"MISSING_SOURCE","MISSING_PURPOSE","MISSING_VISUAL","DURATION_INVALID","BROKEN_DEPENDENCY"}

def check(manifest):
    errors=[]
    units=manifest.get("units",[])
    ids={u["unit_id"] for u in units}
    for u in units:
        if not u.get("source_refs"):
            errors.append(("MISSING_SOURCE",u["unit_id"]))
        if not u.get("purpose"):
            errors.append(("MISSING_PURPOSE",u["unit_id"]))
    for e in manifest.get("dependency_graph",{}).get("edges",[]):
        if e["from"] not in ids or e["to"] not in ids:
            errors.append(("BROKEN_DEPENDENCY",f'{e["from"]}->{e["to"]}'))
    return errors

if __name__=="__main__":
    m=json.loads(Path(sys.argv[1]).read_text())
    errors=check(m)
    print(json.dumps({"status":"PASS" if not errors else "FAIL","errors":errors},indent=2))
    raise SystemExit(1 if errors else 0)
