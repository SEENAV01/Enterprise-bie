import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from script_architect import build_script
def test_script():
 p={"blocks":[{"type":"DEFINITION","objective":"current","evidence_ids":["e1"]}]}
 s=build_script(p,[{"evidence_id":"e1","content":"Current is charge flow"}])
 assert s["units"][0]["type"]=="DEFINITION"
