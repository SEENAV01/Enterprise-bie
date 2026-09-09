from cues import cue

def extract_cues(transcript):
    words=transcript.get("words",[])
    cues=[]
    for i,w in enumerate(words):
        if "start_s" in w:
            cues.append(cue(f"w{i}","WORD",w["start_s"],w.get("word")))
    # Phrase/sentence cues can be supplied by the upstream ASR/NLP layer.
    for i,p in enumerate(transcript.get("phrases",[])):
        cues.append(cue(f"p{i}","PHRASE",p["start_s"],p.get("text"),
                        p.get("confidence",1.0)))
    for i,p in enumerate(transcript.get("pauses",[])):
        cues.append(cue(f"pause{i}","PAUSE",p["start_s"],
                        payload={"duration_s":p.get("duration_s",0)}))
    return sorted(cues,key=lambda x:x["time_s"])
