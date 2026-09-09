class E(ValueError):pass
def sense(term,meaning,scope,anchors,confidence):
 if not all((str(term).strip(),str(meaning).strip(),scope,anchors)) or not 0<=confidence<=1:raise E("sense")
 return {"term":term.strip(),"meaning":meaning.strip(),"scope":scope,"anchors":tuple(dict.fromkeys(anchors)),"confidence":confidence}
