def review_claims(claims):
    invalid=[c.get("claim_id") for c in claims if not c.get("text")]
    return {"total":len(claims),"valid":len(claims)-len(invalid),"invalid":invalid}
def review(checks,claims):
    cr=review_claims(claims)
    return {"checks":checks,"claims":cr,
            "passed":all(v.get("passed",False) for v in checks.values()) and not cr["invalid"]}
