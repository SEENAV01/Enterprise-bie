def registry_entry(service,
                   endpoint,
                   health_status="HEALTHY"):
    return {"service":service,
            "endpoint":endpoint,
            "health_status":health_status}

def discoverable(record):
    return record["endpoint"]["status"]=="ACTIVE" and record["health_status"]=="HEALTHY"
