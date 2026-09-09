import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from store import StateStore
from checkpoints import create_checkpoint,latest_checkpoint
from recovery import recover_from_checkpoint
def test_m268():
 s=StateStore(); a=s.write("x",1); assert a["version"]==1
 assert not s.write("x",2,expected_version=0)["ok"]
 b=s.write("x",2,expected_version=1); assert b["version"]==2
 c=[create_checkpoint("r",1,{"x":1}),create_checkpoint("r",2,{"x":2})]
 assert latest_checkpoint(c,"r")["sequence"]==2
 assert recover_from_checkpoint(c[-1])["ok"]
