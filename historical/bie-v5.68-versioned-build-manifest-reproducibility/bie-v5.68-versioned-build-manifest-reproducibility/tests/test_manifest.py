import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]/"src"))
from manifest import build_manifest
from digest import manifest_digest
from reproducibility import compare_manifests,reproducibility_gate

def test_digest_deterministic():
 m=build_manifest("x",inputs={"a":"1"})
 assert manifest_digest(m)==manifest_digest(dict(m))

def test_gate():
 m=build_manifest("x",inputs={"a":"1"},assets=["a@1"],
                  ir_version="1",generator={"v":"1"},
                  renderer={"v":"1"},dependencies={"x":"1"})
 assert reproducibility_gate(m)["valid"]

def test_difference():
 a={"inputs":{"x":1}}; b={"inputs":{"x":2}}
 assert "inputs" in compare_manifests(a,b)["differences"]
