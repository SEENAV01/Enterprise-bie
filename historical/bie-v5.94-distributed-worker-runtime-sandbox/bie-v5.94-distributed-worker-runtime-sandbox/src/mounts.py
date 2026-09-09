def artifact_mount(artifact_id,mount_path,
                   mode="READ_ONLY"):
    return {"artifact_id":artifact_id,
            "mount_path":mount_path,"mode":mode}

def writable(mount):
    return mount.get("mode")=="READ_WRITE"
