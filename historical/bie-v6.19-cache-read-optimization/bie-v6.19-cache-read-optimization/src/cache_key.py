def cache_key(namespace,entity,
              identifier=None,version=None,
              tenant_id=None):
    parts=[namespace,entity]
    if tenant_id is not None: parts.append(str(tenant_id))
    if identifier is not None: parts.append(str(identifier))
    if version is not None: parts.append(str(version))
    return ":".join(parts)

def valid(key):
    return isinstance(key,str) and bool(key)
