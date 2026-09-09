def integration_adapter(name,
                       provider,protocol,
                       timeout_seconds=30,
                       retryable=True):
    return {"name":name,
            "provider":provider,
            "protocol":protocol,
            "timeout_seconds":timeout_seconds,
            "retryable":retryable}

def adapter_ready(record):
    return bool(record["name"] and record["provider"])
