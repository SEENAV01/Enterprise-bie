def index(index_id,dataset_id,version,
         embedding_model,embedding_version):
    return {"index_id":index_id,"dataset_id":dataset_id,
            "version":version,
            "embedding_model":embedding_model,
            "embedding_version":embedding_version}

def index_ref(index_record):
    return {"index_id":index_record["index_id"],
            "version":index_record["version"],
            "embedding_version":index_record["embedding_version"]}
