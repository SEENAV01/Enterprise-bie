def reconciliation(key,left,right,
                    action="MERGE"):
    if action not in {"MERGE","REPLACE_LEFT","REPLACE_RIGHT","DELETE"}:
        raise ValueError("INVALID_RECONCILIATION_ACTION")
    return {"key":key,"left":left,"right":right,
            "action":action,"status":"PLANNED"}

def applied(record):
    out=dict(record); out["status"]="APPLIED"; return out
