import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from mastery import estimate_mastery
from remediation import remediation_path
def test_m231():
 m=estimate_mastery([{"score":1},{"score":0}])
 assert m["mastery"]==0.5
 assert remediation_path("x",0.4)["action"]=="RETEACH_AND_PRACTICE"
 assert remediation_path("x",0.9)["action"]=="ADVANCE"
