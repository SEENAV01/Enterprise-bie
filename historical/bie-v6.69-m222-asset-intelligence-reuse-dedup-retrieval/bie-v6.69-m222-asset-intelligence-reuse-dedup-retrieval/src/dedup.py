class DedupIndex:
    def __init__(self): self.by_checksum={}
    def register(self,a):
        c=a.get("checksum")
        if not c: return a["asset_id"],False
        if c in self.by_checksum:
            return self.by_checksum[c],True
        self.by_checksum[c]=a["asset_id"]
        return a["asset_id"],False
