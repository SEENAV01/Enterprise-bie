from build import validate_build_environment,build_project
from render_executor import create_render_request,execute_render,validate_render_result
from mp4 import artifact_manifest,validate_mp4_artifact
from qa import render_qa,release_gate
from recovery import recovery_plan,validate_recovery

def build_m254_runtime():
    job={"composition_id":"scene-c-field","output":"dist/lesson.mp4",
         "codec":"h264","fps":30,"duration_in_frames":120}
    build=validate_build_environment("20.x","7.x")
    project=build_project("GeneratedEducationalScene","remotion-project")
    request=create_render_request(job,project["project_dir"])
    result=execute_render(request)
    render=validate_render_result(result)
    artifact=artifact_manifest(result,job["fps"],job["duration_in_frames"])
    artifact_check=validate_mp4_artifact(artifact)
    qa=render_qa(result,job["output"])
    recovery=recovery_plan({"code":"TRANSIENT_RENDER_ERROR"})
    recovery_check=validate_recovery(recovery)
    gate=release_gate(build,render,artifact_check,qa)
    return {"schema_version":"7.01","build_validation":build,"project":project,
            "render_request":request,"render_result":result,
            "render_validation":render,"artifact":artifact,
            "artifact_validation":artifact_check,"render_qa":qa,
            "recovery_plan":recovery,"recovery_validation":recovery_check,
            "release_gate":gate}
