class ArtifactLockManager:
    def __init__(self):
        self._locks={}

    def acquire(self, artifact_id, owner, ttl=60):
        current=self._locks.get(artifact_id)
        if current and current["owner"] != owner:
            return False
        self._locks[artifact_id]={"owner":owner,"ttl":ttl}
        return True

    def release(self, artifact_id, owner):
        current=self._locks.get(artifact_id)
        if not current or current["owner"] != owner:
            return False
        del self._locks[artifact_id]
        return True

    def owner(self, artifact_id):
        current=self._locks.get(artifact_id)
        return current["owner"] if current else None
