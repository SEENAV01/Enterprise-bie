import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from complexity import estimate_complexity
from render_strategy import choose_strategy
from resources import resource_request
def test_m221():
 f={"concepts":5,"equations":3,"diagrams":4,"simulation":2,"3d":0,"code":0}
 c=estimate_complexity(f)
 assert c["level"]=="HIGH"
 assert choose_strategy(c,f)["strategy"]=="HYBRID_2D_SIMULATION"
 assert resource_request(c,{"visual":"HIGH"})["gpu"]>=1
