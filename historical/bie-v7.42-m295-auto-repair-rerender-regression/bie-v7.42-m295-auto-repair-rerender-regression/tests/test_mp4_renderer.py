import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))

from mp4_renderer import validate_render

def test_failed_render_is_not_reported_as_success():
    result={"status":"failed","reason":"REMOTION_RENDER_FAILED","rendered":False,"output":"/tmp/no.mp4"}
    assert validate_render(result)["passed"] is False

def test_success_requires_output_file(tmp_path):
    p=tmp_path/"x.mp4"
    p.write_bytes(b"not-a-real-video")
    result={"status":"success","rendered":True,"output":str(p)}
    assert validate_render(result)["passed"] is True
