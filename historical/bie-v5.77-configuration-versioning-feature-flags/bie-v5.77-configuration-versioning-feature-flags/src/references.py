def config_ref(config_id,version,digest_value):
    return {"config_id":config_id,"version":version,
            "digest":digest_value}

def reproducibility_ref(config,flags=None,
                        experiments=None):
    return {"config":config,
            "feature_flags":flags or [],
            "experiments":experiments or []}
