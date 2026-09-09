STAGE_CONTRACTS = {
    "UNDERSTOOD":["understanding"],
    "PLANNED":["plan"],
    "SCRIPTED":["script"],
    "STORYBOARDED":["storyboard"],
    "ASSETS_READY":["asset_manifest"],
    "AUDIO_READY":["audio_plan"],
    "COMPOSED":["composition"],
    "RENDERED":["rendered_video"],
    "QA_EVALUATED":["quality_report"],
    "VERIFIED":["verification"]
}

def contract(stage):
    return {"stage":stage,"required_artifacts":STAGE_CONTRACTS.get(stage,[])}

def satisfied(stage, artifact_types):
    return all(x in artifact_types for x in STAGE_CONTRACTS.get(stage,[]))
