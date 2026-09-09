def config_value(key,value,
                 value_type="string",
                 source="DEFAULT",
                 scope="GLOBAL"):
    allowed={"string","integer","number","boolean","json"}
    if value_type not in allowed:
        raise ValueError("INVALID_VALUE_TYPE")
    return {"key":key,"value":value,
            "value_type":value_type,
            "source":source,
            "scope":scope}

def typed(record):
    return record["value_type"] in {"string","integer","number","boolean","json"}
