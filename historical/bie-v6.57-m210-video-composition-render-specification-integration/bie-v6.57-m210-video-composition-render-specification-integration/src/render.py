SUPPORTED_FORMATS = {"MP4","WEBM","MOV","PNG_SEQUENCE"}

def render_profile(profile_id, format="MP4", codec="H264",
                   width=1920, height=1080, fps=30,
                   bitrate=None, audio_codec="AAC"):
    if format not in SUPPORTED_FORMATS:
        raise ValueError("UNSUPPORTED_RENDER_FORMAT")
    return {"profile_id":profile_id,"format":format,"codec":codec,
            "width":width,"height":height,"fps":fps,
            "bitrate":bitrate,"audio_codec":audio_codec}

def valid(p):
    return bool(p["profile_id"] and p["format"] in SUPPORTED_FORMATS
                and p["width"] > 0 and p["height"] > 0 and p["fps"] > 0)
