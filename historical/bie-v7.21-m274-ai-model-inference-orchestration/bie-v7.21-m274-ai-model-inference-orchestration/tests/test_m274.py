import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from registry import register_model
from routing import route
from inference import create_inference_job
from cache import cache_key
def test_m274():
 s={}; m=register_model(s,"m","1",["x"],"p",0.1)
 assert route(list(s.values()),"x")["model_id"]=="m"
 j=create_inference_job("j",m,"hello"); assert j["model_version"]=="1"
 assert cache_key("m","1","hello")=="m:1:hello"
