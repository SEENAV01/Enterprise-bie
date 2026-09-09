def messaging_capabilities():
    return {
      "event_envelopes":True,
      "topics":True,
      "subscriptions":True,
      "ordering":True,
      "delivery_guarantees":True,
      "retry_policies":True,
      "dead_letter":True,
      "deduplication":True,
      "consumer_groups":True,
      "acknowledgements":True,
      "messaging_audit":True,
      "messaging_observability":True
    }
