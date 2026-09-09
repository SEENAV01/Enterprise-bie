from project import render_project
from assets import validate_assets
from cache import build_fingerprint,cache_key
from qa import qa_report,output_gate

def compile_render_plan(project_id,entrypoint,composition_id,
                        required_assets,available_assets,
                        spec,duration_seconds,fps,frames,
                        audio_duration=None):
    asset_check=validate_assets(required_assets,available_assets)
    checks=[]
    if audio_duration is not None:
        delta=abs(audio_duration-duration_seconds)
        checks.append({"valid":delta<=0.25,"error":"AUDIO_DURATION_MISMATCH" if delta>0.25 else None})
    expected=round(duration_seconds*fps)
    checks.append({"valid":expected==frames,"error":"FRAME_COUNT_MISMATCH" if expected!=frames else None})
    fingerprint=build_fingerprint(spec)
    key=cache_key(project_id,composition_id,fingerprint)
    project=render_project(project_id,entrypoint,[composition_id],required_assets)
    qa=qa_report({"status":"PLANNED"},asset_check,checks,[])
    return {"schema_version":"5.26","project":project,
            "render":{"composition_id":composition_id,"duration_seconds":duration_seconds,
                      "fps":fps,"frames":frames,"cache_key":key},
            "preflight_qa":qa,"release_gate":output_gate(qa)}
