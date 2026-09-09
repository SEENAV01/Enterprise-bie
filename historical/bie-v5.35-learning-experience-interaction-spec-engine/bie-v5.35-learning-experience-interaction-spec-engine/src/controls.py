def control(control_id,control_type,target,range_spec=None,
            default=None,accessibility=None):
    return {"control_id":control_id,"control_type":control_type,
            "target":target,"range":range_spec,"default":default,
            "accessibility":accessibility or {}}
