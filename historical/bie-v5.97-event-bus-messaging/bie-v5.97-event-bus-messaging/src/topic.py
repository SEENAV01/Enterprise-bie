def topic(topic_id,event_types=None,
          partitions=1,ordering="PARTITION"):
    return {"topic_id":topic_id,
            "event_types":event_types or [],
            "partitions":partitions,
            "ordering":ordering}

def subscription(subscription_id,topic_id,
                 consumer_id,delivery="AT_LEAST_ONCE"):
    return {"subscription_id":subscription_id,
            "topic_id":topic_id,
            "consumer_id":consumer_id,
            "delivery":delivery}
