def find_missing_prerequisites(target, dependencies, known_nodes):
    missing=[]
    for d in dependencies:
        if d["target"]==target and d["type"]=="PREREQUISITE":
            if d["source"] not in known_nodes:
                missing.append(d)
    return missing

def readiness(target, dependencies, known_nodes):
    missing=find_missing_prerequisites(target,dependencies,known_nodes)
    return {
      "target":target,
      "ready":len(missing)==0,
      "missing_prerequisites":missing
    }
