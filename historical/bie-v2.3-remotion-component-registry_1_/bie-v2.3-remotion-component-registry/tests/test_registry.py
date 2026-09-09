import json
from pathlib import Path
def test_contract():
 d=json.loads((Path(__file__).parents[1]/"examples/renderer-contract.json").read_text())
 assert d["scene_dsl"]["renderer"]=="remotion"
 assert d["remotion_manifest"]["duration_in_frames"]>0
