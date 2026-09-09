def validation_contract(contract_id,asset_ref,checks,
                        acceptance=None,review_policy=None):
    return {"contract_id":contract_id,"asset_ref":asset_ref,
            "checks":checks,"acceptance":acceptance or {},
            "review_policy":review_policy or {}}

def acceptance_policy(min_score=None,allow_review=True,
                      required_checks=None):
    return {"min_score":min_score,"allow_review":allow_review,
            "required_checks":required_checks or []}
