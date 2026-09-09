def chunk_document(pages:list[dict],max_chars:int=6000)->list[dict]:
    chunks=[]
    for page in pages:
        text=page.get("text","").strip()
        if not text: continue
        start=0; n=0
        while start<len(text):
            end=min(len(text),start+max_chars)
            chunks.append({
              "chunk_id":f'{page.get("page",0)}-{n}',
              "page":page.get("page"),
              "text":text[start:end],
              "continuation": end<len(text)
            })
            start=end;n+=1
    return chunks
