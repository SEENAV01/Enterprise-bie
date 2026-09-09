def health(service,checks):
    return {"service":service,"checks":checks,
            "healthy":all(checks.values())}

def readiness(checks):
    return all(checks.values())
