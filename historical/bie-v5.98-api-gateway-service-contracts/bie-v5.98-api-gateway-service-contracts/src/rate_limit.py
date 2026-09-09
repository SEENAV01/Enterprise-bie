def rate_limit_policy(name,requests,
                      window_seconds,key="subject"):
    return {"name":name,"requests":requests,
            "window_seconds":window_seconds,"key":key}

def within_limit(count,policy):
    return count < policy["requests"]
