def build_e2e_manifest(wiring,assets,audio,run,logs):
    return {"project":wiring,"assets":assets,"audio":audio,"render_run":run,
            "logs":logs,"status":"READY_FOR_RELEASE"}

def validate_e2e(manifest):
    errors=[]
    if manifest["project"].get("status")!="WIRED": errors.append("PROJECT_NOT_WIRED")
    if manifest["render_run"].get("status")!="SUCCEEDED": errors.append("RENDER_NOT_SUCCEEDED")
    if manifest.get("assets",{}).get("valid") is False: errors.append("ASSET_INJECTION_FAILED")
    if manifest.get("audio",{}).get("valid") is False: errors.append("AUDIO_INJECTION_FAILED")
    return {"valid":not errors,"errors":errors}
