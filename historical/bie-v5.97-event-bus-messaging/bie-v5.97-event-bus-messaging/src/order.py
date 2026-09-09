def message_position(partition,offset):
    return {"partition":partition,"offset":offset}

def ordered(previous,current):
    if previous is None: return True
    if previous["partition"]!=current["partition"]:
        return True
    return current["offset"]>=previous["offset"]
