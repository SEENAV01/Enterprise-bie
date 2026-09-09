def audio_asset(asset_id,audio_type,uri=None,duration=None,
               sample_rate=None,channels=None):
    return {"asset_id":asset_id,"audio_type":audio_type,"uri":uri,
            "duration":duration,"sample_rate":sample_rate,
            "channels":channels}

def audio_cue(cue_id,cue_type,target,offset=0.0,params=None):
    return {"cue_id":cue_id,"cue_type":cue_type,"target":target,
            "offset":offset,"params":params or {}}
