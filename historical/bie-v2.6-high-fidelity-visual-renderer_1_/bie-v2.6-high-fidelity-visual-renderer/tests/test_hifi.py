import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from math_renderer import equation_plan
from camera import camera_plan
def test_hifi():
 assert equation_plan("I=Q/t")["renderer"]=="latex"
 assert camera_plan("slow_push_in")["mode"]=="slow_push_in"
