import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from diagnosis import diagnose
from strategy import select_strategies
from orchestrator import orchestrate
def test_m263():
 d=diagnose(["CONTRAST_BELOW_AA"])
 assert d["actions"]==["ADJUST_TEXT_CONTRAST"]
 assert select_strategies(d["actions"])[0]["target"]=="visual"
 r=orchestrate("s","a",{"valid":False,"errors":["AUDIO_MISSING"]},
               {"valid":True,"errors":[]},2)
 assert r["status"]=="RELEASE_READY"
