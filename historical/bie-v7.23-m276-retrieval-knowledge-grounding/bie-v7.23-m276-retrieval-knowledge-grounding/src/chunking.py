def chunk_document(document, max_words=120, overlap=20):
    words=document["text"].split()
    chunks=[]; start=0; index=0
    step=max(1,max_words-overlap)
    while start<len(words):
        part=words[start:start+max_words]
        chunks.append({"chunk_id":f"{document['document_id']}:chunk:{index}",
                       "document_id":document["document_id"],"index":index,
                       "text":" ".join(part)})
        index+=1; start+=step
    return chunks
