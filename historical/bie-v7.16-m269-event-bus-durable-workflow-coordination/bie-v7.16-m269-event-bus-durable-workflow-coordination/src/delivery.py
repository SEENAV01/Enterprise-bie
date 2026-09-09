def deliver_once(delivery_store,event,subscriber):
    key=f"{subscriber}:{event['event_id']}"
    if key in delivery_store:
        return {"delivered":False,"duplicate":True}
    delivery_store[key]="DELIVERED"
    return {"delivered":True,"duplicate":False}

def delivery_status(delivery_store,event,subscriber):
    return delivery_store.get(f"{subscriber}:{event['event_id']}","PENDING")
