class VersionedStateStore:
    def __init__(self):
        self._data = {}

    def read(self, key):
        return self._data.get(key, {"version":0,"value":None})

    def compare_and_set(self, key, expected_version, value):
        current=self.read(key)
        if current["version"] != expected_version:
            return False
        self._data[key]={"version":expected_version+1,"value":value}
        return True
