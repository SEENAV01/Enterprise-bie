def capability(name,resource_type,action,scope):
    return {"name":name,"resource_type":resource_type,
            "action":action,"scope":scope}

def has_capability(capabilities,name,resource,action):
    return any(c.get("name")==name and
               c.get("resource_type")==resource.get("type") and
               c.get("action")==action and
               c.get("scope")==resource.get("scope")
               for c in capabilities)
