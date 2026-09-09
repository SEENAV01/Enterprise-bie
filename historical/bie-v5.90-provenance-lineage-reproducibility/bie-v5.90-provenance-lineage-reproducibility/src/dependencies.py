def dependency_snapshot(packages=None,assets=None,
                       runtimes=None):
    return {"packages":packages or [],
            "assets":assets or [],
            "runtimes":runtimes or []}

def dependency_ids(snapshot):
    ids=[]
    for group in ("packages","assets","runtimes"):
        ids.extend(x.get("id") for x in snapshot.get(group,[])
                   if isinstance(x,dict) and x.get("id"))
    return ids
