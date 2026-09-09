import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from metadata import build_metadata,validate_metadata
from classification import classify_asset
from fingerprint import perceptual_fingerprint,near_duplicate
from suitability import suitability_score
def test_m273():
 a=build_metadata("a","image",1920,1080)
 assert validate_metadata(a)["valid"]
 assert classify_asset(a)["class"]=="IMAGE"
 f=perceptual_fingerprint([1,2,3]); assert near_duplicate(f,f)
 assert suitability_score(a,{"media_type":"image","min_width":1280})["score"]==1.0
