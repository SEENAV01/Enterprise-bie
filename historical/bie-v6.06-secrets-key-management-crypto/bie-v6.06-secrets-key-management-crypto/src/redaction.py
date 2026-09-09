SENSITIVE_KEYS={"secret","api_key",
                "private_key","password","token"}

def redact(data):
    if not isinstance(data,dict):
        return data
    out={}
    for k,v in data.items():
        out[k]="[REDACTED]" if k in SENSITIVE_KEYS else v
    return out
