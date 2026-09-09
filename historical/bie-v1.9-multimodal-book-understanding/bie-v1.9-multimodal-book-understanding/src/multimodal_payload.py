import json
from pathlib import Path

def build_unit_payload(page_blocks, assets):
    evidence=[]
    for b in page_blocks:
        evidence.append({
            "evidence_id":b["block_id"],
            "page":b["page"],
            "type":b["block_type"],
            "text":b.get("text",""),
            "bbox":b.get("bbox"),
            "asset_ref":b.get("asset_ref")
        })

    visual=[]
    for a in assets:
        visual.append({
            "asset_ref":a["asset_ref"],
            "page":a["page"],
            "type":a["type"],
            "bbox":a.get("bbox"),
            "instruction":(
                "Interpret only what is visibly supported; identify labels, "
                "relationships, quantities and structure. Flag uncertainty."
            )
        })

    return {"evidence":evidence,"visual_assets":visual}
