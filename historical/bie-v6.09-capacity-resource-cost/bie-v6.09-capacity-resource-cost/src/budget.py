def resource_budget(service,
                   compute_units=None,
                   storage_units=None,
                   request_units=None):
    return {"service":service,
            "compute_units":compute_units,
            "storage_units":storage_units,
            "request_units":request_units}

def budget_defined(record):
    return any(v is not None for k,v in record.items()
               if k!="service")
