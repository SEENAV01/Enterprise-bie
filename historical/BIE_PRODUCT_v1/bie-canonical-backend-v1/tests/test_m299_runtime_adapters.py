import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from runtime_adapters import verify_mp4_artifact

def test_missing_mp4_is_rejected(tmp_path):
    r=verify_mp4_artifact(tmp_path/"missing.mp4")
    assert r["status"]=="failed"
    assert r["reason"]=="MP4_ARTIFACT_INVALID"

def test_empty_mp4_is_rejected(tmp_path):
    p=tmp_path/"empty.mp4"; p.write_bytes(b"")
    r=verify_mp4_artifact(p)
    assert r["status"]=="failed"
