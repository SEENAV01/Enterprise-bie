class AssetIndex:
    def __init__(self): self.assets={}
    def add(self,a):
        self.assets[a["asset_id"]]=a
    def get(self,asset_id): return self.assets.get(asset_id)
    def all(self): return list(self.assets.values())
