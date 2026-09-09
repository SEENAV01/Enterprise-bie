def response(response_id,question_id,learner_id,value,
             timestamp=None,attempt=1):
    return {"response_id":response_id,"question_id":question_id,
            "learner_id":learner_id,"value":value,
            "timestamp":timestamp,"attempt":attempt}
