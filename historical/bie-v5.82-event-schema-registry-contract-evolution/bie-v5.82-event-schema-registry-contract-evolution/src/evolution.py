def evolution_plan(event_type,current_version,
                   target_version,compatibility_result):
    breaking=not (compatibility_result.get("backward")
                 and compatibility_result.get("forward"))
    return {"event_type":event_type,
            "from_version":current_version,
            "to_version":target_version,
            "breaking":breaking,
            "strategy":"MIGRATE_OR_DUAL_PUBLISH"
                       if breaking else "ROLL_FORWARD"}

def deprecation(version,replacement=None):
    return {"version":version,"deprecated":True,
            "replacement":replacement}
