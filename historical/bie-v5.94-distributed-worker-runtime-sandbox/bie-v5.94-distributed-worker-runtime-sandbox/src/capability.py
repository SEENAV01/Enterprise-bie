def requirement(capability,minimum=None):
    return {"capability":capability,"minimum":minimum}

def satisfies(worker_record,requirements):
    caps=set(worker_record.get("capabilities",[]))
    return all(r["capability"] in caps for r in requirements)

def resource_satisfies(worker_record,required):
    have=worker_record.get("resources",{})
    return all(have.get(k,0)>=v for k,v in required.items())
