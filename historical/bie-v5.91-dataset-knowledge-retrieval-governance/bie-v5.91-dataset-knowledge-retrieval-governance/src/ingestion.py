def ingestion_run(run_id,dataset_id,source_refs,
                  parser_version,started_at,completed_at=None):
    return {"run_id":run_id,"dataset_id":dataset_id,
            "source_refs":source_refs,
            "parser_version":parser_version,
            "started_at":started_at,
            "completed_at":completed_at}

def ingestion_version(run,sequence):
    return f'{run["run_id"]}:{sequence}'
