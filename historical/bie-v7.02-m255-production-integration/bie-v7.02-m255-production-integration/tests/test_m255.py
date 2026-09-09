import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from project_wiring import wire_remotion_project,validate_project_wiring
from injection import inject_assets,inject_audio
from orchestrator import create_render_run,orchestrate
def test_m255():
 w=wire_remotion_project("p","source")
 assert validate_project_wiring(w)["valid"]
 assert inject_assets([{"asset_id":"a"}],{"a":{"path":"a"}})["valid"]
 assert inject_audio([{"audio_id":"n"}],{"n":{"path":"n.wav"}})["valid"]
 r=orchestrate(create_render_run("r","c"))
 assert r["status"]=="SUCCEEDED" and r["attempt"]==1
