def health_status(service,
                  live=True,ready=True,
                  dependencies=None):
    return {"service":service,
            "live":live,
            "ready":ready,
            "dependencies":dependencies or []}

def is_available(record):
    return record["live"] and record["ready"]
