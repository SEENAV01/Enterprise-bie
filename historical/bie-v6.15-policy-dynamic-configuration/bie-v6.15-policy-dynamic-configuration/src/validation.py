def validation(name,
               config_version,
               checks,
               valid=False):
    return {"name":name,
            "config_version":config_version,
            "checks":checks,
            "valid":valid}

def passed(record):
    return record["valid"] and all(
        c.get("passed",False) for c in record["checks"])
