import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from hashing import sha256
from manifest import manifest,immutable
from replay import replay_plan,replay_ready
from verify import verify_artifact,verify_manifest
from reproducibility import reproduction_fingerprint,compare_fingerprint

def test_hash():
 assert len(sha256({"a":1}))==64

def test_manifest():
 m=immutable(manifest("a",sha256("x"),model={"v":1},
   prompt={"v":1},config={"v":1},code={"v":1}))
 assert verify_manifest(m)
 assert replay_ready(replay_plan(m))

def test_artifact_verify():
 h=sha256("content")
 m=manifest("a",h)
 assert verify_artifact(m,"content")["match"]

def test_fingerprint():
 f=reproduction_fingerprint(1,2,3,4,5,6)
 assert compare_fingerprint(f,f)["match"]
