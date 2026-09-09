def next_version(current):
    parts=[int(x) for x in current.split(".")]
    parts[-1]+=1
    return ".".join(map(str,parts))

def version_record(policy_id,version,change_type,
                   author,reason):
    return {"policy_id":policy_id,"version":version,
            "change_type":change_type,"author":author,
            "reason":reason}
