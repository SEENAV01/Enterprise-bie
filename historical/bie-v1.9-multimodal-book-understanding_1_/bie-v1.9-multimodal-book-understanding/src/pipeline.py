import json,sys
from pathlib import Path
from multimodal_payload import build_unit_payload
from learning_extraction import infer_visual_learning_roles

def run(path,out):
    doc=json.loads(Path(path).read_text())
    pages=doc["pages"]
    blocks=[b for p in pages for b in p.get("blocks",[])]
    assets=doc.get("assets",[])
    payload=build_unit_payload(blocks,assets)
    result={
      "schema_version":"1.9",
      "multimodal_payload":payload,
      "visual_learning_roles":infer_visual_learning_roles(assets),
      "model_stage":"READY_FOR_MULTIMODAL_LLM"
    }
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    run(sys.argv[1],sys.argv[2])
