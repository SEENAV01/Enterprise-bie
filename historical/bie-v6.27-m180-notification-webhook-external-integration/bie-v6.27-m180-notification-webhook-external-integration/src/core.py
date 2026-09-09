"""BIE M180 reference implementation."""

def contract(name, **kwargs):
    return {"name": name, **kwargs, "status": "DEFINED"}

def enabled(record):
    return record.get("status") == "DEFINED"
