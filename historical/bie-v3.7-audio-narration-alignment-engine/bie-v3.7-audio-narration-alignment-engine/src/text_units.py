import re

def tokenize(text):
    return [
      {"index":i,"text":w,"normalized":re.sub(r"[^\w']","",w.lower())}
      for i,w in enumerate(text.split()) if w
    ]

def phrase_units(text, phrases):
    tokens=tokenize(text)
    normalized=[x["normalized"] for x in tokens]
    result=[]
    for phrase in phrases:
        p=[re.sub(r"[^\w']","",x.lower()) for x in phrase.split()]
        for i in range(len(normalized)-len(p)+1):
            if normalized[i:i+len(p)]==p:
                result.append({"phrase":phrase,"start_word":i,"end_word":i+len(p)-1})
    return result
