def injection_request(task_id,grant_id,target,
                     env_name=None,mount_path=None):
    return {"task_id":task_id,"grant_id":grant_id,
            "target":target,"env_name":env_name,
            "mount_path":mount_path}

def injection_boundary(request):
    return {"request":request,
            "payload_contains_raw_secret":False}
