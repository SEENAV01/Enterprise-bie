from pathlib import Path
import shutil, subprocess, json

class AdapterUnavailable(RuntimeError):
    pass

def _cmd_exists(name):
    return shutil.which(name) is not None

def ffmpeg_frame_sample(mp4, output_dir, count=6):
    if not _cmd_exists("ffmpeg"):
        return {"status":"blocked","reason":"FFMPEG_NOT_FOUND","frames":[]}
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    pattern=out/"frame-%02d.jpg"
    p=subprocess.run(
        ["ffmpeg","-y","-i",str(mp4),"-vf",f"fps={count}/10",
         "-frames:v",str(count),str(pattern)],
        capture_output=True,text=True
    )
    frames=sorted(str(x) for x in out.glob("frame-*.jpg"))
    return {"status":"success" if p.returncode==0 and frames else "failed",
            "reason":None if p.returncode==0 and frames else "FRAME_SAMPLE_FAILED",
            "frames":frames}

def tesseract_ocr(frames, output_dir):
    if not _cmd_exists("tesseract"):
        return {"status":"blocked","reason":"TESSERACT_NOT_FOUND","frames":[]}
    out=Path(output_dir); out.mkdir(parents=True,exist_ok=True)
    results=[]
    for frame in frames:
        base=out/Path(frame).stem
        p=subprocess.run(["tesseract",frame,str(base),"tsv"],
                         capture_output=True,text=True)
        tsv=Path(str(base)+".tsv")
        results.append({
            "frame":frame,
            "status":"success" if p.returncode==0 and tsv.exists() else "failed",
            "tsv":str(tsv) if tsv.exists() else None,
            "reason":None if p.returncode==0 and tsv.exists() else "OCR_FAILED"
        })
    return {"status":"success" if results and all(x["status"]=="success" for x in results)
            else "failed","frames":results}

def remotion_command_adapter(project_dir, command):
    if not command:
        return {"status":"blocked","reason":"REMOTION_COMMAND_MISSING"}
    p=subprocess.run(command,cwd=project_dir,capture_output=True,text=True)
    return {"status":"success" if p.returncode==0 else "failed",
            "reason":None if p.returncode==0 else "REMOTION_COMMAND_FAILED",
            "stdout":p.stdout[-2000:],"stderr":p.stderr[-2000:]}

def verify_mp4_artifact(path):
    p=Path(path)
    if not p.exists() or p.stat().st_size<=0:
        return {"status":"failed","reason":"MP4_ARTIFACT_INVALID","path":str(p)}
    ffprobe=shutil.which("ffprobe")
    if not ffprobe:
        return {"status":"success","metadata_verified":False,"path":str(p),
                "note":"FFPROBE_NOT_FOUND"}
    q=subprocess.run([ffprobe,"-v","error","-show_entries",
                      "format=duration,size","-of","json",str(p)],
                     capture_output=True,text=True)
    if q.returncode!=0:
        return {"status":"failed","reason":"FFPROBE_FAILED","path":str(p)}
    return {"status":"success","metadata_verified":True,"path":str(p),
            "metadata":json.loads(q.stdout)}
