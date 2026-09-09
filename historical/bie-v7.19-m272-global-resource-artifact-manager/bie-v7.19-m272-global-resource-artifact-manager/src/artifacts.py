def register_artifact(store, artifact_id, content_hash, metadata=None):
    if artifact_id in store:
        return {"created":False,"artifact":store[artifact_id]}
    item={"artifact_id":artifact_id,"content_hash":content_hash,
          "metadata":metadata or {},"immutable":True}
    store[artifact_id]=item
    return {"created":True,"artifact":item}

def resolve(store, artifact_id):
    return store.get(artifact_id)
