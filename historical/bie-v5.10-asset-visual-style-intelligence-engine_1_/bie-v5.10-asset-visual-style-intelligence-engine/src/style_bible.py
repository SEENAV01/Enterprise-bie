def style_bible(style_id, name, tokens=None, rules=None):
    return {
      "style_id":style_id,"name":name,
      "tokens":tokens or {},
      "rules":rules or {}
    }

def style_token(name,value,scope="GLOBAL"):
    return {"name":name,"value":value,"scope":scope}
