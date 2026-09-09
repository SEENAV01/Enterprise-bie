import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from models import model_profile
from requirements import task_requirements
from decision import route

def test_route():
 models=[
  model_profile("a","p",["TEXT"],quality=.95,cost_per_unit=.1,
                latency_ms=100,reliability=.99),
  model_profile("b","p",["TEXT"],quality=.90,cost_per_unit=.01,
                latency_ms=100,reliability=.99)]
 req=task_requirements("x","TEXT",min_quality=.9)
 r=route(models,req)
 assert r["status"]=="ROUTED"
 assert r["primary"] in {"a","b"}

def test_no_capability():
 m=model_profile("a","p",["IMAGE"])
 req=task_requirements("x","TEXT")
 assert route([m],req)["status"]=="NO_COMPATIBLE_MODEL"
