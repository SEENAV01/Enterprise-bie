from pathlib import Path
import json
import hashlib
import subprocess
import shutil

def canonical_text(value):
    return " ".join(str(value or "").split()).strip()

def extract_expected_visual_requirements(scene_dsl):
    req=[]
    for scene in scene_dsl.get("scenes",[]):
        for visual in scene.get("visuals",[]):
            typ=visual.get("type")
            if typ in {"equation","diagram","title","source_text"}:
                req.append({
                    "scene_id":scene.get("scene_id"),
                    "type":typ,
                    "expected_text":canonical_text(visual.get("text",""))
                })
    return req

def compare_expected_text(expected, ocr_words):
    detected=" ".join(w.get("text","") for w in ocr_words)
    expected_text=canonical_text(expected)
    detected_text=canonical_text(detected)
    e=expected_text.lower()
    d=detected_text.lower()
    if not e:
        return {"status":"not_applicable","match":True,"expected":"","detected":detected_text}
    return {
        "status":"matched" if e in d else "mismatch",
        "match":e in d,
        "expected":expected_text,
        "detected":detected_text
    }

def semantic_compare(scene_dsl, ocr_report):
    expected=extract_expected_visual_requirements(scene_dsl)
    frames=ocr_report.get("frames",[]) if ocr_report.get("status")=="success" else []
    all_words=[]
    for frame in frames:
        if frame.get("status")=="success":
            all_words.extend(frame.get("words",[]))

    comparisons=[]
    for item in expected:
        c=compare_expected_text(item["expected_text"],all_words)
        c.update({"scene_id":item["scene_id"],"type":item["type"]})
        comparisons.append(c)

    mismatches=[c for c in comparisons if c["status"]=="mismatch"]
    return {
        "passed":not mismatches,
        "status":"verified" if expected and not mismatches else
                 ("mismatch" if mismatches else "not_proven"),
        "comparisons":comparisons,
        "mismatch_count":len(mismatches)
    }

def build_repair_patch(scene_dsl, semantic_report):
    patches=[]
    for c in semantic_report.get("comparisons",[]):
        if c.get("status")=="mismatch":
            patches.append({
                "scene_id":c.get("scene_id"),
                "type":c.get("type"),
                "action":"restore_expected_visual_text",
                "expected_text":c.get("expected",""),
                "detected_text":c.get("detected","")
            })
    return {
        "version":"1.0",
        "patches":patches,
        "automatic_application_allowed":False
    }

def apply_safe_repairs(scene_dsl, patch):
    """
    Safe repair only changes visual text to the already-grounded expected text.
    It does not invent content.
    """
    result=json.loads(json.dumps(scene_dsl))
    changed=0
    by_scene={p["scene_id"]:p for p in patch.get("patches",[])}
    for scene in result.get("scenes",[]):
        p=by_scene.get(scene.get("scene_id"))
        if not p:
            continue
        for visual in scene.get("visuals",[]):
            if visual.get("type")==p.get("type"):
                if canonical_text(visual.get("text","")) != canonical_text(p.get("expected_text","")):
                    visual["text"]=p.get("expected_text","")
                    changed+=1
    return result, changed

def hash_dsl(scene_dsl):
    raw=json.dumps(scene_dsl,ensure_ascii=False,sort_keys=True).encode()
    return hashlib.sha256(raw).hexdigest()
