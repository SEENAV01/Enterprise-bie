import json
import os
from pathlib import Path
from bie_product import BIEProduct, tool_manifest
from bie_product.server import create_server

class FakeProvider:
    def healthcheck(self): return {"provider":"fake","ready":True}
    def generate_json(self, **kwargs):
        schema=kwargs["schema_name"]
        return {"task":kwargs["task"],"provider":"fake","model":"test","result":_fixture(schema)}

def _fixture(name):
    if name == "bie_book_knowledge": return {"concepts":[],"relationships":[],"definitions":[],"coverage_notes":[]}
    if name == "bie_lesson_plan": return {"title":"Test","objectives":[],"units":[],"unresolved_items":[]}
    if name == "bie_script": return {"sections":[],"unresolved_items":[]}
    if name == "bie_scene_plan": return {"scenes":[],"unresolved_items":[]}
    raise AssertionError(name)

def test_contract_and_tool_manifest():
    c=json.loads(Path("bie_product/product_contract.json").read_text())
    assert c["core"] == "canonical-m1-m300"
    assert set(c["surfaces"]) == {"http_api","openai_agent_tool","standalone_web_app"}
    assert tool_manifest()["tools"][0]["name"] == "bie_book_to_video_code"

def test_product_health_with_fake_provider(tmp_path):
    p=BIEProduct(work_dir=tmp_path, provider=FakeProvider())
    h=p.health()
    assert h["engine"] == "canonical-m1-m300"
    assert h["provider"]["ready"] is True

def test_server_constructs(tmp_path):
    s=create_server(port=0, work_dir=str(tmp_path))
    try:
        assert s.product.health()["product"] == "BIE"
    finally:
        s.server_close()
