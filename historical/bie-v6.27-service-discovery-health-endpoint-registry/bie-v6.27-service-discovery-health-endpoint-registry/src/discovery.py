def discovery_query(service_name,
                   version=None,
                   region=None,zone=None,
                   healthy_only=True):
    return {"service_name":service_name,
            "version":version,
            "region":region,
            "zone":zone,
            "healthy_only":healthy_only}

def matches(query,service,health_status="HEALTHY"):
    if service["name"] != query["service_name"]:
        return False
    if query["version"] is not None and service["version"] != query["version"]:
        return False
    if query["region"] is not None and service["region"] != query["region"]:
        return False
    if query["zone"] is not None and service["zone"] != query["zone"]:
        return False
    return not query["healthy_only"] or health_status=="HEALTHY"
