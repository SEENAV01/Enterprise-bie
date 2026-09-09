def backpressure_policy(
        max_inflight,
        queue_high_watermark,
        queue_low_watermark):
    return {"max_inflight":max_inflight,
            "queue_high_watermark":queue_high_watermark,
            "queue_low_watermark":queue_low_watermark}

def should_throttle(policy,inflight,depth):
    return (inflight>=policy["max_inflight"] or
            depth>=policy["queue_high_watermark"])
