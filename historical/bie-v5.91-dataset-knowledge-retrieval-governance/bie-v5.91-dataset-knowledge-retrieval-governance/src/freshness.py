def freshness_record(resource_id,observed_at,
                    source_updated_at=None,max_age_seconds=None):
    return {"resource_id":resource_id,
            "observed_at":observed_at,
            "source_updated_at":source_updated_at,
            "max_age_seconds":max_age_seconds}

def is_stale(record,now):
    max_age=record.get("max_age_seconds")
    if max_age is None: return False
    return now-record["observed_at"]>max_age
