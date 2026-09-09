SUPPORTED_CHECKS = {
    "FILE_EXISTS","DURATION","FRAME_COUNT","RESOLUTION",
    "FPS","AUDIO_PRESENT","AUDIO_SYNC","CAPTION_SYNC",
    "SCENE_COVERAGE","BLACK_FRAMES","FREEZE_FRAMES",
    "CORRUPTION","CHECKSUM"
}

def qa_check(check_id, check_type, target_ref, expected=None,
             observed=None, status="PASS", details=None):
    if check_type not in SUPPORTED_CHECKS:
        raise ValueError("UNSUPPORTED_QA_CHECK")
    if status not in {"PASS","FAIL","REVIEW"}:
        raise ValueError("INVALID_QA_STATUS")
    return {"check_id":check_id,"check_type":check_type,
            "target_ref":target_ref,"expected":expected,
            "observed":observed,"status":status,"details":details}

def passed(c):
    return c["status"]=="PASS"
