class StateStore:
    def __init__(self):
        self.data={}

    def read(self,key):
        item=self.data.get(key)
        return None if item is None else dict(item)

    def write(self,key,value,expected_version=None):
        current=self.data.get(key)
        actual=0 if current is None else current["version"]
        if expected_version is not None and expected_version!=actual:
            return {"ok":False,"error":"VERSION_CONFLICT","actual_version":actual}
        version=actual+1
        self.data[key]={"version":version,"value":value}
        return {"ok":True,"version":version,"value":value}
