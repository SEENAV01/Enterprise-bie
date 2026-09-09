def health_signal(service,status,
                 timestamp,latency_ms=None,
                 error_rate=None):
    return {"service":service,"status":status,
            "timestamp":timestamp,
            "latency_ms":latency_ms,
            "error_rate":error_rate}
