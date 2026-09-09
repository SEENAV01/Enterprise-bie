def deduplicate(store, content_hash):
    return [a for a in store.values() if a["content_hash"]==content_hash]

def canonical_artifact(store, content_hash):
    matches=deduplicate(store,content_hash)
    return matches[0] if matches else None
