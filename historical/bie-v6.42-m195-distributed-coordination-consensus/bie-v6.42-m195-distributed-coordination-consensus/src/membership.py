def membership(epoch_id, members, change_type="STABLE"):
    if change_type not in {"STABLE","ADD","REMOVE","REPLACE"}:
        raise ValueError("INVALID_MEMBERSHIP_CHANGE")
    return {"epoch_id":epoch_id,"members":members,
            "change_type":change_type}

def contains(record, participant_id):
    return participant_id in record["members"]
