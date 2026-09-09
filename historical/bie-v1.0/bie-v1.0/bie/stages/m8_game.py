
def run(lesson):
    games=[]
    for i,item in enumerate(lesson["assessment"],1):
        games.append({"game_id":f"G{i:02d}","game_type":"adaptive_quiz",
                      "learning_targets":item["refs"],"source_refs":item.get("source_refs",[]),
                      "mastery_threshold":.85})
    return {"games":games}
