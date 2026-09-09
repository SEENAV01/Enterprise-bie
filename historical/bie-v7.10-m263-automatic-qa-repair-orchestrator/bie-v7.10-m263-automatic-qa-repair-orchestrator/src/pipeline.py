from diagnosis import diagnose
from orchestrator import orchestrate

def build_m263_runtime():
    initial={"valid":False,"errors":["CONTRAST_BELOW_AA","AUDIO_LOUDNESS_OUT_OF_RANGE"]}
    diagnosis=diagnose(initial["errors"])
    result=orchestrate("scene-c-field","field-media",initial,
                       revalidation_result={"valid":True,"errors":[]},max_cycles=2)
    gate={"valid":result["status"]=="RELEASE_READY","status":result["status"],
          "errors":[] if result["status"]=="RELEASE_READY" else ["QA_REPAIR_EXHAUSTED"]}
    return {"schema_version":"7.10","initial_qa":initial,"diagnosis":diagnosis,
            "orchestration":result,"repair_gate":gate}
