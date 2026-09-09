from pathlib import Path
import json, subprocess, shutil, hashlib

def _run(cmd, cwd=None):
    return subprocess.run(cmd,cwd=cwd,capture_output=True,text=True)

def regenerate_remotion(project_dir, generator_cmd):
    """Run the project's declared generator. Never claims success without exit 0."""
    if not generator_cmd:
        return {"status":"blocked","reason":"REMOTION_GENERATOR_COMMAND_MISSING"}
    proc=_run(generator_cmd, cwd=project_dir)
    return {
        "status":"success" if proc.returncode==0 else "failed",
        "reason":None if proc.returncode==0 else "REMOTION_REGENERATION_FAILED",
        "stdout":proc.stdout[-3000:],"stderr":proc.stderr[-3000:]
    }

def render_second_pass(project_dir, render_cmd, expected_mp4):
    if not render_cmd:
        return {"status":"blocked","reason":"REMOTION_RENDER_COMMAND_MISSING"}
    proc=_run(render_cmd,cwd=project_dir)
    path=Path(expected_mp4)
    ok=proc.returncode==0 and path.exists() and path.stat().st_size>0
    return {
        "status":"success" if ok else "failed",
        "reason":None if ok else "SECOND_RENDER_FAILED",
        "output":str(path),
        "size":path.stat().st_size if path.exists() else 0,
        "stdout":proc.stdout[-3000:],"stderr":proc.stderr[-3000:]
    }

def regression_decision(before_semantic, after_semantic):
    b=before_semantic.get("mismatch_count",0)
    a=after_semantic.get("mismatch_count",0)
    after_status=after_semantic.get("status","not_proven")
    if after_status=="mismatch":
        return {"decision":"reject","reason":"SEMANTIC_MISMATCH_REMAINS",
                "mismatches_before":b,"mismatches_after":a}
    if a>b:
        return {"decision":"reject","reason":"REGRESSION_INCREASED",
                "mismatches_before":b,"mismatches_after":a}
    if after_status=="verified" and a==0:
        return {"decision":"accept","reason":"SEMANTIC_QA_PASSED",
                "mismatches_before":b,"mismatches_after":a}
    return {"decision":"review","reason":"SEMANTIC_RESULT_NOT_PROVEN",
            "mismatches_before":b,"mismatches_after":a}

def execute_actual_cycle(project_dir,generator_cmd,render_cmd,expected_mp4,
                         before_semantic,after_semantic_provider):
    regen=regenerate_remotion(project_dir,generator_cmd)
    if regen["status"]!="success":
        return {"status":"blocked","regeneration":regen}
    render=render_second_pass(project_dir,render_cmd,expected_mp4)
    if render["status"]!="success":
        return {"status":"failed","regeneration":regen,"render":render}
    after=after_semantic_provider(Path(expected_mp4))
    decision=regression_decision(before_semantic,after)
    return {"status":"complete","regeneration":regen,"render":render,
            "after_semantic":after,"decision":decision}
