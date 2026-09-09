def visual_grammar(grammar_id, conventions=None):
    return {
      "grammar_id":grammar_id,
      "conventions":conventions or {}
    }

def convention(name, meaning, examples=None):
    return {"name":name,"meaning":meaning,"examples":examples or []}
