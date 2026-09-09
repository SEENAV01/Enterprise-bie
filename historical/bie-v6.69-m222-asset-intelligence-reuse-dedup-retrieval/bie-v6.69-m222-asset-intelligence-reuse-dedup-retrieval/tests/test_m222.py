import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from asset import asset,valid
from index import AssetIndex
from dedup import DedupIndex
from retrieval import retrieve
def test_m222():
 a=asset("a","diagram","asset://a",{"subject":"electric field"},
         ["electric","field"],"sha256:x")
 assert valid(a)
 i=AssetIndex(); i.add(a)
 d=DedupIndex(); d.register(a)
 b=asset("b","diagram","asset://b",checksum="sha256:x")
 assert d.register(b)[1]
 assert retrieve(i,"electric field")[0]["asset_id"]=="a"
