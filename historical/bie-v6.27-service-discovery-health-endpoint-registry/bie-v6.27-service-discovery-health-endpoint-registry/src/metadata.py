def service_metadata(service_id,
                    labels=None,attributes=None):
    return {"service_id":service_id,
            "labels":labels or {},
            "attributes":attributes or {}}

def has_label(record,key,value):
    return record["labels"].get(key)==value
