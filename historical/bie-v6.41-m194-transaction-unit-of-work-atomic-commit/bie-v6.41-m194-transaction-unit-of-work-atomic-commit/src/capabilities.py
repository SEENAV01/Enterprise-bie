def transaction_capabilities():
    return {
      "transaction_scopes":True,
      "unit_of_work":True,
      "read_write_sets":True,
      "prepare":True,
      "commit":True,
      "rollback":True,
      "conflict_detection":True,
      "idempotency":True,
      "savepoints":True,
      "transaction_audit":True,
      "transaction_observability":True
    }
