import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from assets import asset,asset_ref
from media import media_metadata,validate_metadata
from transform import transform_step
from composition import composition,composition_input
from pipeline import pipeline,add_step,complete
from quality import media_quality_check,validate_media

def test_asset():
 a=asset("a","IMAGE","hash","image/png")
 assert asset_ref(a)["asset_id"]=="a"

def test_metadata():
 assert validate_metadata("IMAGE",media_metadata(1920,1080))
 assert validate_metadata("VIDEO",media_metadata(duration=10))

def test_pipeline():
 p=add_step(pipeline("a"),transform_step("s","resize",
   [{"asset_id":"a"}],{"asset_id":"b"}))
 assert complete(p,[{"asset_id":"b"}])["status"]=="COMPLETE"

def test_quality():
 assert validate_media([media_quality_check("ok",True)])["passed"]
