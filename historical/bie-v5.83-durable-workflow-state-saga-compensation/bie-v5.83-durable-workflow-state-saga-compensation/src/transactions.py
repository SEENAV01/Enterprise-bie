def transaction_result(completed,failed=None):
    return {"completed":completed,
            "failed":failed,
            "partial_failure":failed is not None}

def requires_compensation(result):
    return bool(result.get("completed")) and result.get("failed") is not None
