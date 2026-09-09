def accessibility_metadata(language="en",captions=True,
                           audio_description=False,transcript=True):
    return {"language":language,"captions":captions,
            "audio_description":audio_description,"transcript":transcript}

def accessibility_check(meta):
    errors=[]
    if not meta.get("captions"): errors.append("CAPTIONS_NOT_DECLARED")
    if not meta.get("transcript"): errors.append("TRANSCRIPT_NOT_DECLARED")
    return {"valid":not errors,"errors":errors}
