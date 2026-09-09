def version_record(record,version,change_summary=None):
    updated=dict(record)
    updated["version"]=version
    updated["change_summary"]=change_summary
    return updated

def is_compatible(record,min_version=None,max_version=None):
    # Reference implementation leaves semantic version parsing to a production adapter.
    return {"compatible":True,"record_version":record.get("version"),
            "min_version":min_version,"max_version":max_version}
