def safe_update_plan(key,current,
                    new_value,expected_version):
    return {"key":key,
            "from_version":current.get("version"),
            "to_version":current.get("version",0)+1,
            "expected_version":expected_version,
            "new_value":new_value,
            "preconditions":["VALIDATE_TYPE",
                             "CHECK_VERSION",
                             "AUDIT_CHANGE"]}
