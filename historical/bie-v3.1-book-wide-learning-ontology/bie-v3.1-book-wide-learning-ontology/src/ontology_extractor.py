from question_axes import AXES,empty_axis

def classify_statement(statement):
    text=statement.lower()
    scores={a:0 for a in AXES}
    if any(x in text for x in ["is ","are ","means ","defined"]): scores["what"]+=2
    if any(x in text for x in ["because","due to","therefore","purpose"]): scores["why"]+=2
    if any(x in text for x in ["how ","process","method","step","derive"]): scores["how"]+=2
    if any(x in text for x in ["when","during","after","before","year"]): scores["when"]+=2
    if any(x in text for x in ["where","located","region","place"]): scores["where"]+=2
    if any(x in text for x in ["who","person","scientist","author"]): scores["who"]+=2
    if any(x in text for x in ["greater","less","choose","type","kind"]): scores["which"]+=1
    if any(x in text for x in ["rate","amount","mass","value","percent","number"]): scores["how_much"]+=1
    return max(scores,key=scores.get) if max(scores.values()) else "what"

def make_learning_unit(text,evidence_id):
    axis=classify_statement(text)
    return {
      "text":text,
      "primary_axis":axis,
      "axes":{a:empty_axis(a) for a in AXES},
      "evidence_ids":[evidence_id],
      "status":"EXTRACTED"
    }
