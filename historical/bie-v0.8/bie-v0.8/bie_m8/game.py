
GAME_MAP={
 "definition":"mcq",
 "fact":"mcq",
 "process":"ordering",
 "mechanism":"cause_effect",
 "derivation":"derivation_order",
 "comparison":"matching",
 "application":"prediction",
 "data":"graph_interpretation",
 "simulation":"simulation",
 "question":"adaptive_quiz",
 "concept":"mcq"
}

def choose_game(kind, application=False):
    return "prediction" if application else GAME_MAP.get(kind,"adaptive_quiz")

def build_game(targets, game_type=None, difficulty=.5):
    if not targets: raise ValueError("At least one learning target is required")
    kind=game_type or choose_game(targets[0].get("kind","concept"), targets[0].get("is_application",False))
    return {
      "game_id":"G_AUTO",
      "learning_targets":[x["id"] for x in targets],
      "game_type":kind,
      "difficulty":difficulty,
      "mechanics":{
        "attempts":3,
        "hint":True,
        "feedback":"explain_error",
        "mastery_tracking":True
      },
      "content":[
        {"target":x["id"],"prompt":x.get("prompt",f"Demonstrate understanding of {x['id']}"),
         "correct":x.get("correct"),"distractors":x.get("distractors",[]),
         "source_refs":x.get("source_refs",[])}
        for x in targets
      ],
      "feedback":{"correct":"reinforce_reasoning","incorrect":"show_reason_and_retry"},
      "adaptation":{
        "on_mastery":"increase_difficulty",
        "on_failure":"reduce_difficulty_and_add_prerequisite_review",
        "mastery_threshold":.85
      },
      "source_refs":[r for x in targets for r in x.get("source_refs",[])],
      "validation":{"requires_source_support":True,"requires_single_unambiguous_answer":True}
    }

def compile_game(game):
    # Runtime-neutral IR: front-end/game engine can consume this without regenerating content.
    return {
      "runtime":"BIEGameRuntime",
      "gameId":game["game_id"],
      "type":game["game_type"],
      "difficulty":game["difficulty"],
      "targets":game["learning_targets"],
      "mechanics":game["mechanics"],
      "items":game["content"],
      "feedback":game["feedback"],
      "adaptation":game["adaptation"]
    }

def build_adaptive_path(history, base_difficulty=.5):
    if not history:return base_difficulty
    recent=history[-5:]
    score=sum(x.get("correct",False) for x in recent)/len(recent)
    if score>=.8:return min(1,base_difficulty+.1)
    if score<=.4:return max(0,base_difficulty-.15)
    return base_difficulty
