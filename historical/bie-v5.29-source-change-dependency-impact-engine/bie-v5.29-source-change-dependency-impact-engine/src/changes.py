def source_change(change_id,source_ref,change_type,
                  before_hash=None,after_hash=None,description=None):
    return {"change_id":change_id,"source_ref":source_ref,
            "change_type":change_type,"before_hash":before_hash,
            "after_hash":after_hash,"description":description}
