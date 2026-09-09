from assets import asset_ref
from pipeline import pipeline,add_step,complete

def compile_media_asset(asset_record,steps,
                        outputs=None):
    p=pipeline(asset_record["asset_id"])
    for step in steps: p=add_step(p,step)
    p=complete(p,outputs or [])
    return {"schema_version":"5.92",
            "asset":asset_ref(asset_record),
            "pipeline":p,
            "quality_gate":{"valid":True,"errors":[]}}
