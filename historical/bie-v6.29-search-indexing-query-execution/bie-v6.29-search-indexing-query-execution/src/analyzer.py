def analyzer(name,tokenizer="STANDARD",
             filters=None):
    allowed={"STANDARD","WHITESPACE","KEYWORD"}
    if tokenizer not in allowed:
        raise ValueError("INVALID_TOKENIZER")
    return {"name":name,"tokenizer":tokenizer,
            "filters":filters or []}

def analyze(record,text):
    if record["tokenizer"]=="KEYWORD":
        return [text]
    return text.split()
