def canonical_config(profile="default", provider=None,
                     renderer="remotion", qa_profile="standard"):
    return {"profile":profile,"provider":provider,
            "renderer":renderer,"qa_profile":qa_profile,
            "schema_version":"6.48"}

def compatible(config):
    return config["renderer"]=="remotion" and bool(config["profile"])
