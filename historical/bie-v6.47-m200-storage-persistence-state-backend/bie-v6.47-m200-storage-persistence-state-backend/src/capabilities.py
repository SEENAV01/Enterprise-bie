def storage_capabilities():
    return {
      "key_value_records":True,
      "blobs":True,
      "collections":True,
      "namespaces":True,
      "versioning":True,
      "conditional_writes":True,
      "transactions":True,
      "snapshots":True,
      "consistency":True,
      "storage_audit":True,
      "storage_observability":True
    }
