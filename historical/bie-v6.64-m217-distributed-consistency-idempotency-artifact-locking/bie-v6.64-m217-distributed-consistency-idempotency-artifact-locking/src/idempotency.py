class IdempotencyStore:
    def __init__(self):
        self._records = {}

    def begin(self, key, fingerprint):
        if key in self._records:
            record = self._records[key]
            if record["fingerprint"] != fingerprint:
                raise ValueError("IDEMPOTENCY_CONFLICT")
            return record
        record = {"key":key,"fingerprint":fingerprint,
                  "status":"IN_PROGRESS","result":None}
        self._records[key] = record
        return record

    def complete(self, key, result):
        if key not in self._records:
            raise ValueError("UNKNOWN_IDEMPOTENCY_KEY")
        self._records[key]["status"]="COMPLETED"
        self._records[key]["result"]=result
        return self._records[key]

    def get(self, key):
        return self._records.get(key)
