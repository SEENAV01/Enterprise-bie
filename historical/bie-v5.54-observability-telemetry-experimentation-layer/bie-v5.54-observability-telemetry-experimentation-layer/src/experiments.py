def experiment(experiment_id,name,hypothesis,variants,
               metrics,allocation=None):
    return {"experiment_id":experiment_id,"name":name,
            "hypothesis":hypothesis,"variants":variants,
            "metrics":metrics,"allocation":allocation or {}}

def assignment(experiment_id,subject_id,variant):
    return {"experiment_id":experiment_id,
            "subject_id":subject_id,"variant":variant}
