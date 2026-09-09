def contract_test(name,
                 provider_contract,
                 consumer,
                 expected_status=200):
    return {"name":name,
            "provider_contract":provider_contract,
            "consumer":consumer,
            "expected_status":expected_status,
            "status":"DEFINED"}

def pass_test(record):
    out=dict(record); out["status"]="PASSED"; return out
