def scope(name,parent=None,priority=0):
    return {"name":name,"parent":parent,"priority":priority}

def hierarchy(scopes):
    return sorted(scopes,key=lambda x:x["priority"],reverse=True)
