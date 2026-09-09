def residency(resource_id,
              allowed_regions,
              actual_region):
    return {"resource_id":resource_id,
            "allowed_regions":allowed_regions,
            "actual_region":actual_region,
            "compliant":actual_region in allowed_regions}

def compliant(record):
    return bool(record["compliant"])
