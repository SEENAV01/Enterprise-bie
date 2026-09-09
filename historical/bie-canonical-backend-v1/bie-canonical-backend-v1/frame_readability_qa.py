from pathlib import Path
import json
import shutil
import subprocess

def sample_frames(render_result, output_dir, fps=30, sample_count=6):
    """Create evenly spaced frame samples when ffmpeg is available."""
    output = render_result.get("output")
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    if not render_result.get("rendered") or not output:
        return {"status":"blocked","reason":"RENDER_ARTIFACT_MISSING","frames":[]}

    ffmpeg = shutil.which("ffmpeg")
    if not ffmpeg:
        return {"status":"blocked","reason":"FFMPEG_NOT_FOUND","frames":[]}

    # Use ffmpeg fps filter; cap the number of generated samples.
    pattern = out / "frame-%02d.jpg"
    proc = subprocess.run(
        [ffmpeg, "-y", "-i", str(output), "-vf",
         f"fps={max(1, sample_count)}/10", "-frames:v", str(sample_count),
         str(pattern)],
        capture_output=True, text=True
    )
    frames = sorted(str(p) for p in out.glob("frame-*.jpg"))
    return {
        "status":"success" if proc.returncode == 0 and frames else "failed",
        "reason":None if proc.returncode == 0 and frames else "FRAME_SAMPLING_FAILED",
        "frames":frames,
        "stdout":proc.stdout[-2000:],
        "stderr":proc.stderr[-2000:]
    }

def estimate_readability(frame_sampling):
    """
    Conservative image-level checks. Without OCR/model inference, this reports
    measurable image properties only and never invents OCR results.
    """
    try:
        from PIL import Image
    except ImportError:
        return {"status":"blocked","reason":"PIL_NOT_FOUND","checks":[]}

    checks=[]
    for path in frame_sampling.get("frames",[]):
        p=Path(path)
        try:
            with Image.open(p) as im:
                width,height=im.size
                checks.append({
                    "frame":str(p),
                    "width":width,
                    "height":height,
                    "pixels":width*height,
                    "readability_status":"image_available_for_review"
                })
        except Exception as exc:
            checks.append({
                "frame":str(p),
                "readability_status":"decode_failed",
                "error":str(exc)
            })
    return {"status":"success","checks":checks}

def build_readability_report(frame_sampling, readability):
    errors=[]
    if frame_sampling.get("status") != "success":
        errors.append(frame_sampling.get("reason","FRAME_SAMPLING_FAILED"))
    if not readability.get("checks") and frame_sampling.get("status") == "success":
        errors.append("NO_FRAME_READABILITY_CHECKS")
    for check in readability.get("checks",[]):
        if check.get("readability_status") == "decode_failed":
            errors.append("FRAME_DECODE_FAILED")
    return {
        "passed":not errors,
        "errors":sorted(set(errors)),
        "sample_count":len(readability.get("checks",[])),
        "checks":readability.get("checks",[])
    }

def generate_readability_repair_plan(report):
    repairs=[]
    for error in report.get("errors",[]):
        if error in {"FFMPEG_NOT_FOUND","PIL_NOT_FOUND"}:
            repairs.append({"action":"install_runtime_dependency","reason":error})
        elif error=="RENDER_ARTIFACT_MISSING":
            repairs.append({"action":"rerender","reason":error})
        elif error in {"FRAME_DECODE_FAILED","FRAME_SAMPLING_FAILED"}:
            repairs.append({"action":"resample_frames","reason":error})
        else:
            repairs.append({"action":"manual_visual_review","reason":error})
    return {
        "version":"1.0",
        "repairs":repairs,
        "automatic_repairs_applied":False
    }
