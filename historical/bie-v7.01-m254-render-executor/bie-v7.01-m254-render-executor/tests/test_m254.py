import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from render_executor import create_render_request,execute_render,validate_render_result
from mp4 import artifact_manifest,validate_mp4_artifact
from recovery import classify_failure
def test_m254():
 j={"composition_id":"s","output":"x.mp4","codec":"h264","fps":30,"duration_in_frames":10}
 r=execute_render(create_render_request(j,"p"))
 assert validate_render_result(r)["valid"]
 a=artifact_manifest(r,30,10)
 assert validate_mp4_artifact(a)["valid"]
 assert classify_failure("RENDER_TIMEOUT")["retryable"]
