import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from adaptive import choose_action
def test_adaptive():
 assert choose_action(.4)=="RETEACH"
 assert choose_action(.95)=="ADVANCE"
