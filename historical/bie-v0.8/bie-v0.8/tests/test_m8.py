
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from bie_m8.game import build_game,compile_game,build_adaptive_path

def test_game():
    g=build_game([{"id":"x","kind":"process","source_refs":["p"]}])
    assert g["game_type"]=="ordering"
    assert g["validation"]["requires_source_support"]

def test_compile():
    g=build_game([{"id":"x","kind":"concept"}])
    assert compile_game(g)["runtime"]=="BIEGameRuntime"

def test_adaptive():
    assert build_adaptive_path([{"correct":True}]*5)>.5
    assert build_adaptive_path([{"correct":False}]*5)<.5
