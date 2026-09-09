def trigger_workflow(event,rules):
    actions=[]
    for rule in rules:
        if rule["event_type"]==event["event_type"]:
            actions.append({"workflow":rule["workflow"],"input":event["payload"]})
    return actions
