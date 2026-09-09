import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from asset_intelligence import make_record
def test_asset():
 r=make_record("x",{"width":1400,"height":900,"ocr_confidence":.97,"has_caption":True,"caption":"diagram","ocr_text":"diagram","source_page":1})
 assert r["reuse_policy"]=="REUSE_SOURCE"
