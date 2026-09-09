def publish(store,evt):
    store.append(evt)
    return evt["event_id"]

def read(store,after=0):
    return store[after:]

def subscribe(subscriptions,event_type,handler):
    subscriptions.setdefault(event_type,[]).append(handler)
