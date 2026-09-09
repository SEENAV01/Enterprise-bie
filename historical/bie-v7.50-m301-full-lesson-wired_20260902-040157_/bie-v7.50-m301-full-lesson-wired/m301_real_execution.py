from pathlib import Path
import json, shutil, subprocess, time

def executable(name):
    return shutil.which(name)

def dependency_report():
    return {
        "node": executable("node"),
        "npm": executable("npm"),
        "npx": executable("npx"),
        "ffmpeg": executable("ffmpeg"),
        "ffprobe": executable("ffprobe"),
        "tesseract": executable("tesseract"),
    }

def run_command(cmd, cwd=None, timeout=120):
    p=subprocess.run(cmd,cwd=cwd,capture_output=True,text=True,timeout=timeout)
    return {
        "status":"success" if p.returncode==0 else "failed",
        "returncode":p.returncode,
        "stdout":p.stdout[-4000:],
        "stderr":p.stderr[-4000:]
    }

def validate_source(path):
    p=Path(path)
    return {"status":"success","path":str(p),"size":p.stat().st_size} if p.exists() and p.stat().st_size else {
        "status":"failed","reason":"SOURCE_MISSING_OR_EMPTY","path":str(p)
    }

def validate_mp4(path):
    p=Path(path)
    if not p.exists() or p.stat().st_size==0:
        return {"status":"failed","reason":"MP4_MISSING_OR_EMPTY","path":str(p)}
    if executable("ffprobe"):
        r=run_command(["ffprobe","-v","error","-show_entries","format=duration,size","-of","json",str(p)])
        if r["status"]!="success":
            return {"status":"failed","reason":"FFPROBE_FAILED","path":str(p)}
        return {"status":"success","path":str(p),"metadata":json.loads(r["stdout"])}
    return {"status":"success","path":str(p),"metadata_verified":False}

def acceptance(artifacts, qa):
    missing=[k for k,v in artifacts.items() if not v or (isinstance(v,str) and not Path(v).exists())]
    return {
        "accepted":not missing and qa.get("status")=="accepted",
        "missing":missing,
        "qa":qa
    }
