def media_quality_check(name,passed,metric=None,
                       threshold=None):
    return {"name":name,"passed":bool(passed),
            "metric":metric,"threshold":threshold}

def validate_media(checks):
    return {"checks":checks,
            "passed":all(c["passed"] for c in checks)}
