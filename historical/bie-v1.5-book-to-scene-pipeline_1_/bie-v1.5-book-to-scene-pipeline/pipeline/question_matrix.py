QUESTION_KINDS=["what","why","how","when","where","who","derivation","application"]

def matrix(unit:dict)->dict:
    found={k:[] for k in QUESTION_KINDS}
    for q in unit.get("questions",[]):
        if q["kind"] in found: found[q["kind"]].append(q["qid"])
    return found

def coverage(book_ir:dict)->dict:
    return {u["unit_id"]:matrix(u) for u in book_ir["units"]}
