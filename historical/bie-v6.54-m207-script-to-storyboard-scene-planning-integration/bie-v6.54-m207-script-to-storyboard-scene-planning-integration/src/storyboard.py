from scene import ordered

def storyboard(storyboard_id, script_id, scenes,
               canvas="1920x1080", visual_style="educational"):
    return {"storyboard_id":storyboard_id,"script_id":script_id,
            "scenes":ordered(scenes),"canvas":canvas,
            "visual_style":visual_style}

def valid(item):
    return bool(item["storyboard_id"] and item["script_id"] and item["scenes"])
