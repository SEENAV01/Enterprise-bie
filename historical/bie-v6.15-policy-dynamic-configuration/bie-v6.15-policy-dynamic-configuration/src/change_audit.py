def change_audit(change_id,
                config_name,from_version,
                to_version,actor,reason):
    return {"change_id":change_id,
            "config_name":config_name,
            "from_version":from_version,
            "to_version":to_version,
            "actor":actor,
            "reason":reason}
