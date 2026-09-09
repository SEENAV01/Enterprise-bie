import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_spatial_scene

def test_valid():
 c={"scene_id":"s","objects":[
  {"object_id":"a","box":{"x":10,"y":10,"width":10,"height":10}}],
  "constraints":[]}
 assert compile_spatial_scene(c)["quality_gate"]["valid"]

def test_overlap():
 c={"scene_id":"s","objects":[
  {"object_id":"a","box":{"x":0,"y":0,"width":20,"height":20}},
  {"object_id":"b","box":{"x":10,"y":10,"width":20,"height":20}}],
  "constraints":[]}
 assert not compile_spatial_scene(c)["quality_gate"]["valid"]
