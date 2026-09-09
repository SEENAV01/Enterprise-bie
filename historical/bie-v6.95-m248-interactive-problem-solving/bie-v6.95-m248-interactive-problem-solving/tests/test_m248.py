import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from state import create_state
from step_validation import validate_step
from dynamic_hints import next_hint_level
from session import process_turn
def test_m248():
 s=create_state("p",["a","b"])
 assert validate_step("a","a")["valid"]
 assert next_hint_level("CONCEPT",{"valid":False})=="STRATEGY"
 r=process_turn(s,"bad","a","do a")
 assert r["action"]=="HINT"
 r=process_turn(s,"a","a","do a")
 assert r["action"]=="ADVANCE" and s["current_step"]==1
