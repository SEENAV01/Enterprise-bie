def evaluation_record(evaluation_id,model_id,
                     suite_id,suite_version,rubric_id,
                     rubric_version,config_ref=None):
    return {"schema_version":"5.79",
            "evaluation_id":evaluation_id,
            "model_id":model_id,"suite_id":suite_id,
            "suite_version":suite_version,
            "rubric_id":rubric_id,
            "rubric_version":rubric_version,
            "config_ref":config_ref}
