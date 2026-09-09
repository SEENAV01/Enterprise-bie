import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registry import register_asset,resolve_asset
from versioning import asset_fingerprint
from dedupe import deduplicate_assets
def test_m259():
 r={}
 a=register_asset(r,"a","image","x.png","1")
 assert resolve_asset(r,"a","1")["id"]=="a"
 f=asset_fingerprint(a)
 assert deduplicate_assets([{"id":"a","fingerprint":f},{"id":"b","fingerprint":f}])["aliases"]["b"]=="a"
