def dataset(dataset_id,version,source_refs=None,
            access_policy=None,freshness=None):
    return {"dataset_id":dataset_id,"version":version,
            "source_refs":source_refs or [],
            "access_policy":access_policy,
            "freshness":freshness,
            "schema_version":"5.91"}

def snapshot(dataset_record):
    return {"dataset_id":dataset_record["dataset_id"],
            "version":dataset_record["version"],
            "source_refs":dataset_record.get("source_refs",[])}
