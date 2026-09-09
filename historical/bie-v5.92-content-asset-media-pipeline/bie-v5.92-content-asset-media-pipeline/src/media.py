def media_metadata(width=None,height=None,duration=None,
                  codec=None,frame_rate=None,sample_rate=None,
                  channels=None):
    return {"width":width,"height":height,"duration":duration,
            "codec":codec,"frame_rate":frame_rate,
            "sample_rate":sample_rate,"channels":channels}

def validate_metadata(kind,meta):
    if kind=="IMAGE":
        return meta.get("width",0)>0 and meta.get("height",0)>0
    if kind=="VIDEO":
        return meta.get("duration",0)>=0
    if kind=="AUDIO":
        return meta.get("duration",0)>=0
    return True
