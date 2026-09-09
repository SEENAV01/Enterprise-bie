def dedup_index():
    return {}

def register(index,content_id,artifact_id):
    index.setdefault(content_id,[]).append(artifact_id)
    return index

def duplicates(index,content_id):
    return index.get(content_id,[])
