import json
from pathlib import Path

def validate(path):
    x=json.loads(Path(path).read_text())
    assert x["lesson_id"]
    assert x["scenes"]
    for s in x["scenes"]:
        assert s["duration_frames"] > 0
        assert s["source_refs"]
        assert s["visual"]["type"]
        assert s["timeline"]
    return True

if __name__=="__main__":
    import sys
    validate(sys.argv[1])
    print("Scene DSL: VALID")
