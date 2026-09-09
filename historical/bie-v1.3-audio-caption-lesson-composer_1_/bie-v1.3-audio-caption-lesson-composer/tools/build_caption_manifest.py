import json, re, sys
from pathlib import Path

src=Path(sys.argv[1])
out=Path(sys.argv[2])
data=json.loads(src.read_text())
manifest={"lesson_id":data["lesson_id"],"scenes":[]}

for s in data["scenes"]:
    script=s["narration"].get("script","")
    words=re.findall(r"\S+",script)
    duration=s["narration"].get("estimated_duration_frames") or s["duration_frames"]
    step=max(2,duration//max(1,len(words)))
    captions=[{"text":w,"startFrame":i*step,"endFrame":min(duration,(i+1)*step+2)} for i,w in enumerate(words)]
    manifest["scenes"].append({
        "scene_id":s["scene_id"],
        "audio_asset":s["narration"].get("audio_asset"),
        "caption_words":captions,
        "duration_frames":s["duration_frames"]
    })
out.write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
print(out)
