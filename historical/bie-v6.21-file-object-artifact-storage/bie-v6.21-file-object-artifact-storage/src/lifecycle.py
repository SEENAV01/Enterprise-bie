def lifecycle_policy(object_id,
                    states=None,
                    archive_after=None,
                    delete_after=None):
    return {"object_id":object_id,
            "states":states or
            ["ACTIVE","ARCHIVED","DELETED"],
            "archive_after":archive_after,
            "delete_after":delete_after}

def transition_allowed(current,next_state):
    allowed={
      "ACTIVE":{"ARCHIVED","DELETED"},
      "ARCHIVED":{"ACTIVE","DELETED"},
      "DELETED":set()
    }
    return next_state in allowed.get(current,set())
