from alignment import validate_alignment

def compile_audio_sync(script,alignments=None,captions=None,
                       anchors=None,audio_assets=None,speech=None):
    errors=[]
    for a in alignments or []:
        errors.extend(validate_alignment(a))
    segment_ids={s["segment_id"] for s in script.get("segments",[])}
    for a in alignments or []:
        if a.get("segment_id") not in segment_ids:
            errors.append("ALIGNMENT_SEGMENT_MISSING")
    return {"schema_version":"5.41",
            "script":script,"alignments":alignments or [],
            "captions":captions or [],"anchors":anchors or [],
            "audio_assets":audio_assets or [],"speech_plan":speech or {},
            "quality_gate":{"valid":not errors,
                            "errors":sorted(set(errors))}}
