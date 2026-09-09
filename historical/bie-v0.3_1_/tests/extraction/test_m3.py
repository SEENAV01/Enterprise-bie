from backend.extraction.m3_extractor import _validate

def test_provenance_is_required():
    r = _validate({"units":[{"id":"u1","type":["fact"],"statement":"x","questions":["WHAT"],"source_block_ids":["missing"],"confidence":.9}],"relations":[]},{"b1"})
    assert r.units == []
    assert any("provenance" in w for w in r.warnings)

def test_unknown_relation_is_removed():
    payload={"units":[{"id":"u1","type":["fact"],"statement":"x","questions":["WHAT"],"source_block_ids":["b1"],"confidence":.9}],"relations":[{"source_id":"u1","relation":"CAUSES","target_id":"u2","confidence":.8}]}
    r=_validate(payload,{"b1"})
    assert r.relations == []
