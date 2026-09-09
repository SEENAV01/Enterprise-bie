def enqueue(queue,case):
    out=list(queue); out.append(case)
    out.sort(key=lambda x:-x.get("priority",0))
    return out
