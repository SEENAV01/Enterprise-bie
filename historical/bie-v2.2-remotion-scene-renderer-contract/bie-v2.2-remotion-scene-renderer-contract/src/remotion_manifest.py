def build_manifest(compiled):
    timeline=[]
    frame=0
    fps=compiled.get("fps",30)
    for s in compiled["scenes"]:
        frames=round(s["duration_ms"]*fps/1000)
        timeline.append({
            "scene_id":s["scene_id"],
            "from":frame,
            "duration_in_frames":frames,
            "type":s["type"]
        })
        frame+=frames
    return {
        "composition_id":"BIECourse",
        "fps":fps,
        "width":compiled["resolution"]["width"],
        "height":compiled["resolution"]["height"],
        "duration_in_frames":frame,
        "timeline":timeline
    }
