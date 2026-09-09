def catalog_entry(resource_id, schema_id=None,
                  metadata_id=None, lineage_ref=None):
    return {"resource_id":resource_id,"schema_id":schema_id,
            "metadata_id":metadata_id,"lineage_ref":lineage_ref}

def indexed(record):
    return bool(record["resource_id"])
