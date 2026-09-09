import re

def normalize(text):
    text=re.sub(r"[^a-z0-9 ]","",text.lower())
    return " ".join(text.split())

def duplicate_score(a,b):
    x=normalize(a.get("text",a.get("label","")))
    y=normalize(b.get("text",b.get("label","")))
    if not x or not y:return 0.0
    sx=set(x.split()); sy=set(y.split())
    return len(sx&sy)/max(1,len(sx|sy))

def cluster_duplicates(items, threshold=0.75):
    clusters=[]
    for item in items:
        placed=False
        for cluster in clusters:
            if duplicate_score(item,cluster[0])>=threshold:
                cluster.append(item); placed=True; break
        if not placed: clusters.append([item])
    return clusters
