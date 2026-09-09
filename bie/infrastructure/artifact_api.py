
class ArtifactAPIError(ValueError):pass
class ArtifactAPI:
 def __init__(self,catalog,blob_store):self.catalog=catalog;self.blobs=blob_store
 def metadata(self,artifact_id):
  x=self.catalog.get(artifact_id)
  if x is None:raise ArtifactAPIError("artifact not found")
  return x
 def content(self,artifact_id):
  m=self.metadata(artifact_id);return self.blobs.get(m["content_hash"])
 def lineage(self,artifact_id):
  self.metadata(artifact_id);return tuple(self.catalog.parents(artifact_id))
