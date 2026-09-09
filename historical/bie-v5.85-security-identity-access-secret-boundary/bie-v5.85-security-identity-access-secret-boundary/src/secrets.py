def secret_ref(secret_id,provider="SECRET_STORE",
               version=None):
    return {"secret_id":secret_id,"provider":provider,
            "version":version}

def validate_secret_ref(ref):
    return bool(ref.get("secret_id")) and bool(ref.get("provider"))

def redact(value):
    return "[REDACTED]" if value is not None else None
