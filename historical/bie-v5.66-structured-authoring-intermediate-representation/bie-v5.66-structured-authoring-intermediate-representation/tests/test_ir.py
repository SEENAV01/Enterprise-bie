import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from compiler import compile_ir
from bindings import resolve_bindings

def test_ir_compile():
 ir={"lessons":[{"scenes":[{"components":[
  {"component_id":"x","component_type":"TEXT"}]}]}]}
 assert compile_ir(ir)["quality_gate"]["valid"]

def test_binding():
 b={"semantic_ref":"force","target_ref":"label"}
 assert resolve_bindings([b],{"force":10})[0]["value"]==10
