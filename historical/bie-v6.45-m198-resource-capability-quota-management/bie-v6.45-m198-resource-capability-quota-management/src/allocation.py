def allocation(allocation_id, reservation_id,
                resource, amount):
    if amount <= 0:
        raise ValueError("INVALID_ALLOCATION_AMOUNT")
    return {"allocation_id":allocation_id,
            "reservation_id":reservation_id,
            "resource":resource,"amount":amount,
            "status":"ALLOCATED"}

def allocated(record):
    return record["status"]=="ALLOCATED"
