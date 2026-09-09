from pathlib import Path
import json
import subprocess
import shutil

def inspect_render(render_result):
    """
    Lightweight render artifact inspection.
    It validates existence/size and, when available, uses ffprobe to inspect
    duration/streams. It does not claim semantic visual correctness.
    """
    output = render_result.get("output")
    if not render_result.get("rendered") or not output:
        return {"passed":False,"errors":["render_artifact_missing"],"metrics":{}}

    p=Path(output)
    if not p.exists():
        return {"passed":False,"errors":["render_artifact_missing"],"metrics":{}}

    errors=[]
    metrics={"file_size_bytes":p.stat().st_size}
    if metrics["file_size_bytes"] <= 0:
        errors.append("empty_render_artifact")

    ffprobe=shutil.which("ffprobe")
    if ffprobe:
        proc=subprocess.run(
            [ffprobe,"-v","error","-show_entries",
             "format=duration:stream=codec_type,width,height",
             "-of","json",str(p)],
            capture_output=True,text=True
        )
        if proc.returncode==0:
            try:
                data=json.loads(proc.stdout)
                metrics["ffprobe"]=data
                duration=float(data.get("format",{}).get("duration",0) or 0)
                if duration <= 0:
                    errors.append("non_positive_duration")
            except (ValueError, TypeError):
                errors.append("ffprobe_parse_failed")
        else:
            errors.append("ffprobe_failed")
    else:
        metrics["ffprobe_available"]=False

    return {"passed":not errors,"errors":errors,"metrics":metrics}

def generate_repair_plan(scene_dsl, visual_report):
    repairs=[]
    for error in visual_report.get("errors",[]):
        if error=="empty_render_artifact":
            repairs.append({"action":"rerender","reason":error})
        elif error=="non_positive_duration":
            repairs.append({"action":"inspect_timing","reason":error})
        elif error=="render_artifact_missing":
            repairs.append({"action":"rerender","reason":error})
        else:
            repairs.append({"action":"inspect_render_pipeline","reason":error})
    return {
        "repair_plan_version":"1.0",
        "repairs":repairs,
        "automatic_repairs_applied":False,
        "policy":"never mutate source claims during visual repair"
    }

def validate_visual_qa(report, repair_plan):
    errors=[]
    if not isinstance(report.get("errors",[]),list):
        errors.append("invalid_visual_errors")
    if not isinstance(repair_plan.get("repairs",[]),list):
        errors.append("invalid_repair_plan")
    return {"passed":not errors,"errors":errors}
