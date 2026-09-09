def pronunciation(term, phonetic=None, aliases=None,
                   language=None, notes=None):
    return {"term":term,"phonetic":phonetic,"aliases":aliases or [],
            "language":language,"notes":notes}

def valid(item):
    return bool(item["term"])
