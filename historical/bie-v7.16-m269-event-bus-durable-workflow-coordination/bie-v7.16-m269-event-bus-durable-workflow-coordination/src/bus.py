def publish(bus,event):
    bus.setdefault("topics",{}).setdefault(event["event_type"],[]).append(event)
    return {"accepted":True,"event_id":event["event_id"]}

def subscribe(bus,subscriber,event_type):
    bus.setdefault("subscriptions",{}).setdefault(subscriber,set()).add(event_type)
    return {"subscriber":subscriber,"event_type":event_type,"status":"SUBSCRIBED"}

def poll(bus,subscriber,event_type):
    events=bus.get("topics",{}).get(event_type,[])
    return [e for e in events if event_type in bus.get("subscriptions",{}).get(subscriber,set())]
