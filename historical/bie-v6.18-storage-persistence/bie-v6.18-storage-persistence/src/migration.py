def migration(migration_id,
              from_version,to_version,
              operations):
    return {"migration_id":migration_id,
            "from_version":from_version,
            "to_version":to_version,
            "operations":operations,
            "status":"PLANNED"}

def applied(record):
    out=dict(record); out["status"]="APPLIED"; return out
