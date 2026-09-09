def authorization_capabilities():
    return {
      "principals":True,
      "roles":True,
      "permissions":True,
      "resource_scopes":True,
      "authorization_decisions":True,
      "delegation":True,
      "service_identities":True,
      "credential_boundaries":True,
      "authorization_audit":True
    }
