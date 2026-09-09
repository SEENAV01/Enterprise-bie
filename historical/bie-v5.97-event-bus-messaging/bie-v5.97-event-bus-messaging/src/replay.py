def replay_request(topic_id,start_offset,
                  end_offset=None,consumer_id=None):
    return {"topic_id":topic_id,
            "start_offset":start_offset,
            "end_offset":end_offset,
            "consumer_id":consumer_id}

def replayable(request):
    return request.get("start_offset") is not None
