SCHEMA_VERSION="6.48"

REQUIRED_STAGES=[
 "source","understanding","knowledge","pedagogy","lesson",
 "script","storyboard","scene","assets","audio","remotion",
 "render","qa","publish"
]

def stage_contract(stage, status="PENDING", input_ref=None,
                   output_ref=None, errors=None):
    if stage not in REQUIRED_STAGES:
        raise ValueError("UNKNOWN_STAGE")
    return {"stage":stage,"status":status,
            "input_ref":input_ref,"output_ref":output_ref,
            "errors":errors or []}

def valid_stage(record):
    return record["stage"] in REQUIRED_STAGES
