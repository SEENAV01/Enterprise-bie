import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registry import register
from assets import asset
from staleness import impacted_assets

def test_register():
 r={"assets":[],"relations":[]}
 r=register(r,asset("a","1","IMAGE"))
 assert r["assets"][0]["asset_id"]=="a"

def test_impact():
 r={"relations":[
  {"source":"a@1","target":"b@1"},
  {"source":"b@1","target":"c@1"}]}
 assert impacted_assets(r,["a@1"])==["a@1","b@1","c@1"]
