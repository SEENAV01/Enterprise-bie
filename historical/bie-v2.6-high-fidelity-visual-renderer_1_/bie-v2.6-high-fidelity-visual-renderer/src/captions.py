def caption_plan(markers, max_chars=42):
    captions=[]
    current=[]
    for m in markers:
        token=m.get("token","")
        if sum(len(x)+1 for x in current)+len(token) > max_chars and current:
            captions.append({"text":" ".join(current),"start_ms":None,"end_ms":None})
            current=[]
        current.append(token)
    if current:
        captions.append({"text":" ".join(current),"start_ms":None,"end_ms":None})
    return captions
