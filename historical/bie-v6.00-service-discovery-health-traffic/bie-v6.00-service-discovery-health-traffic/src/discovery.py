def discover(registry,service_name,
             require_version=None):
    records=list(registry.get(service_name,{}).values())
    if require_version is not None:
        records=[r for r in records
                 if r.get("version")==require_version]
    return [r for r in records if r.get("status")!="DRAINING"]

def mark_health(record,health_status):
    out=dict(record)
    out["status"]=health_status
    return out
