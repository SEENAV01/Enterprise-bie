def subscription(subscription_id, topic_id,
                  consumer_group=None, filter_expression=None):
    return {"subscription_id":subscription_id,
            "topic_id":topic_id,
            "consumer_group":consumer_group,
            "filter_expression":filter_expression,
            "status":"ACTIVE"}

def active(record):
    return record["status"]=="ACTIVE"
