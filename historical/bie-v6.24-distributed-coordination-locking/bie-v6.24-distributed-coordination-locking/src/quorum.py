def quorum(total_nodes,
           required=None):
    if total_nodes < 1:
        raise ValueError("INVALID_NODE_COUNT")
    required = required if required is not None else total_nodes//2+1
    if not 1 <= required <= total_nodes:
        raise ValueError("INVALID_QUORUM")
    return {"total_nodes":total_nodes,
            "required":required}

def reached(record,acks):
    return acks >= record["required"]
