from pathlib import Path
import shutil
import subprocess
import json

def detect_ocr_engine():
    return shutil.which("tesseract")

def run_ocr(frame_paths, output_dir):
    """Run OCR when Tesseract is available; otherwise return an explicit blocked state."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    tesseract = detect_ocr_engine()
    if not tesseract:
        return {"status":"blocked","reason":"TESSERACT_NOT_FOUND","frames":[]}

    results=[]
    for frame in frame_paths:
        p=Path(frame)
        base=out/p.stem
        proc=subprocess.run(
            [tesseract,str(p),str(base),"tsv"],
            capture_output=True,text=True
        )
        tsv=Path(str(base)+".tsv")
        if proc.returncode != 0 or not tsv.exists():
            results.append({
                "frame":str(p),"status":"failed",
                "reason":"OCR_FAILED","stderr":proc.stderr[-1000:]
            })
            continue

        words=[]
        lines=tsv.read_text(encoding="utf-8",errors="replace").splitlines()
        if lines:
            header=lines[0].split("\t")
            idx={name:i for i,name in enumerate(header)}
            for row in lines[1:]:
                cols=row.split("\t")
                if len(cols) <= max(idx.values(), default=0):
                    continue
                text=cols[idx.get("text", -1)].strip() if idx.get("text",-1)>=0 else ""
                try:
                    conf=float(cols[idx.get("conf",-1)])
                except (ValueError, TypeError):
                    conf=-1
                if text and conf >= 0:
                    words.append({
                        "text":text,
                        "confidence":conf,
                        "left":int(cols[idx["left"]]),
                        "top":int(cols[idx["top"]]),
                        "width":int(cols[idx["width"]]),
                        "height":int(cols[idx["height"]])
                    })
        results.append({"frame":str(p),"status":"success","words":words})
    return {"status":"success","frames":results}

def analyze_text_boxes(ocr_result, min_confidence=50):
    checks=[]
    errors=[]
    if ocr_result.get("status") != "success":
        return {"passed":False,"errors":[ocr_result.get("reason","OCR_UNAVAILABLE")],"checks":[]}

    for frame in ocr_result.get("frames",[]):
        if frame.get("status") != "success":
            errors.append("OCR_FAILED")
            continue
        words=frame.get("words",[])
        low=[w for w in words if w.get("confidence",-1) < min_confidence]
        checks.append({
            "frame":frame["frame"],
            "word_count":len(words),
            "low_confidence_word_count":len(low),
            "ocr_status":"available"
        })
    return {"passed":not errors,"errors":sorted(set(errors)),"checks":checks}

def validate_ocr_contract(ocr_result, bbox_report):
    errors=[]
    if ocr_result.get("status")=="success":
        for f in ocr_result.get("frames",[]):
            for w in f.get("words",[]):
                for key in ("left","top","width","height"):
                    if key not in w:
                        errors.append("MISSING_BBOX_FIELD")
    if not isinstance(bbox_report.get("checks",[]),list):
        errors.append("INVALID_BBOX_REPORT")
    return {"passed":not errors,"errors":sorted(set(errors))}

def generate_ocr_repair_plan(bbox_report):
    repairs=[]
    for error in bbox_report.get("errors",[]):
        if error=="TESSERACT_NOT_FOUND":
            repairs.append({"action":"install_ocr_engine","reason":error})
        elif error=="OCR_FAILED":
            repairs.append({"action":"rerun_ocr","reason":error})
        else:
            repairs.append({"action":"inspect_text_rendering","reason":error})
    return {"version":"1.0","repairs":repairs,"automatic_repairs_applied":False}
