import hashlib

def bucket(subject,flag_id):
    raw=f"{flag_id}:{subject}".encode()
    return int(hashlib.sha256(raw).hexdigest(),16)%100

def eligible(subject,flag):
    if not active(flag):
        return False
    return bucket(subject,flag["flag_id"]) < flag.get("rollout",0)

def active(flag):
    return flag.get("enabled",False) and not flag.get("kill_switch",False)
