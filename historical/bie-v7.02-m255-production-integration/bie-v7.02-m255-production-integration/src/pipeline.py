from project_wiring import wire_remotion_project,validate_project_wiring
from injection import inject_assets,inject_audio
from orchestrator import create_render_run,orchestrate
from logging import log_event,summarize_logs
from e2e import build_e2e_manifest,validate_e2e

def build_m255_runtime():
    source='GeneratedEducationalScene'
    assets=inject_assets([{"id":"diagram","asset_id":"field"}],
                         {"field":{"path":"assets/field.svg","type":"svg"}})
    audio=inject_audio([{"id":"n1","audio_id":"narration-1"}],
                       {"narration-1":{"path":"audio/n1.wav","duration":3.0}})
    wiring=wire_remotion_project("remotion-project",source,assets["layers"],audio["segments"])
    wiring_check=validate_project_wiring(wiring)
    run=create_render_run("run-001","scene-c-field")
    run=orchestrate(run)
    events=[log_event(run["run_id"],"INFO","End-to-end render completed",
                      {"attempt":run["attempt"]})]
    logs=summarize_logs(events)
    manifest=build_e2e_manifest(wiring,assets,audio,run,logs)
    gate=validate_e2e(manifest)
    return {"schema_version":"7.02","wiring":wiring,"wiring_validation":wiring_check,
            "asset_injection":assets,"audio_injection":audio,"render_run":run,
            "logs":logs,"e2e_manifest":manifest,"integration_gate":gate}
