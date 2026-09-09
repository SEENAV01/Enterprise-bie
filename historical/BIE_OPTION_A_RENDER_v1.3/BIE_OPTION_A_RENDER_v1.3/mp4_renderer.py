from pathlib import Path
import shutil
import subprocess
import json

def find_npx():
    return shutil.which("npx")

def render_mp4(project_meta, output_dir, timeout_seconds=300):
    project_dir = Path(project_meta["project_dir"])
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    mp4 = out / "bie-lesson.mp4"

    npx = find_npx()
    if not npx:
        return {
            "status":"blocked",
            "reason":"NODE_NPX_NOT_FOUND",
            "output":str(mp4),
            "rendered":False
        }

    try:
        proc = subprocess.run(
            [npx, "remotion", "render", "src/index.tsx",
             project_meta["composition_id"], str(mp4)],
            cwd=project_dir,
            capture_output=True, text=True, timeout=timeout_seconds
        )
    except subprocess.TimeoutExpired as e:
        return {
            "status":"failed","reason":"RENDER_TIMEOUT","rendered":False,
            "stdout":e.stdout or "","stderr":e.stderr or "","output":str(mp4)
        }

    return {
        "status":"success" if proc.returncode == 0 and mp4.exists() else "failed",
        "reason":None if proc.returncode == 0 and mp4.exists() else "REMOTION_RENDER_FAILED",
        "returncode":proc.returncode,
        "rendered":mp4.exists(),
        "output":str(mp4),
        "stdout":proc.stdout[-4000:],
        "stderr":proc.stderr[-4000:]
    }

def validate_render(result):
    errors=[]
    if result.get("status") != "success":
        errors.append(result.get("reason","UNKNOWN_RENDER_ERROR"))
    output=result.get("output")
    if result.get("rendered") and (not output or not Path(output).exists()):
        errors.append("render-result-file-missing")
    return {"passed":not errors,"errors":errors}
