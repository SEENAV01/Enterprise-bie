def migration(event_type,from_version,to_version,
              transform_name):
    return {"event_type":event_type,
            "from_version":from_version,
            "to_version":to_version,
            "transform":transform_name}

def apply_migration(payload,transform):
    return transform(payload)
