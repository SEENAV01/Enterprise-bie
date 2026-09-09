import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from config import config,validate
from overlay import overlay,resolve
from flag import feature_flag
from rollout import eligible
from update import update_request,apply_update

def test_typed_config():
 assert validate(config("x",True,"boolean"))

def test_overlay():
 assert resolve([overlay("base",{"x":1},0),
                  overlay("prod",{"x":2},1)])["x"]==2

def test_rollout():
 f=feature_flag("f",True,100)
 assert eligible("user-1",f)

def test_safe_update():
 c=config("x",1,"integer",version=2)
 u=update_request("x",2,2)
 assert apply_update(c,u)["version"]==3
