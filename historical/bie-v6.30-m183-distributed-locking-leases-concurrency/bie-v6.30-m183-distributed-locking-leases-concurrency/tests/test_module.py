import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import *

def test_module_contract():
    data = compile_m183()
    assert data["quality_gate"]["valid"] is True
    assert len(data["capabilities"]) >= 1
