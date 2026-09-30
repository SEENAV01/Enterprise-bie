"""Source-bound graph artifact readers for Section 18 viewers."""
from __future__ import annotations
from bie.infrastructure.artifact_store import BlobRef
from bie.infrastructure.persistence import PersistenceError
import json
class GraphArtifactError(ValueError):pass
def _unique_object(pairs):
    out={}
    for k,v in pairs:
        if k in out:raise GraphArtifactError("duplicate json key")
        out[k]=v
    return out
class GraphArtifactViewer:
    TYPES={"concept":"knowledge.concept_graph","prerequisite":"knowledge.prerequisite_graph"}
    def __init__(self,persistence,cas):self.persistence=persistence;self.cas=cas
    def load(self,run_id,artifact_id,kind):
        if kind not in self.TYPES:raise GraphArtifactError("unsupported graph kind")
        try:r=self.persistence.load_artifact(artifact_id)
        except PersistenceError as exc:raise GraphArtifactError("graph artifact not found") from exc
        if r.run_id!=run_id:raise GraphArtifactError("graph artifact belongs to different run")
        if r.artifact_type!=self.TYPES[kind]:raise GraphArtifactError("graph artifact type mismatch")
        raw=self.cas.get_bytes(BlobRef(r.blob_algorithm,r.blob_digest,r.blob_size))
        if len(raw)>4*1024*1024:raise GraphArtifactError("graph artifact too large")
        try:v=json.loads(raw.decode("utf-8"),object_pairs_hook=_unique_object)
        except (UnicodeError,json.JSONDecodeError) as exc:raise GraphArtifactError("invalid graph json") from exc
        if type(v) is not dict or set(v)!={"schema_version","nodes","edges"} or v["schema_version"]!="bie.graph.v1":raise GraphArtifactError("invalid graph envelope")
        if type(v["nodes"]) is not list or type(v["edges"]) is not list:raise GraphArtifactError("invalid graph collections")
        if len(v["nodes"])>5000 or len(v["edges"])>20000:raise GraphArtifactError("graph limits exceeded")
        ids=set();nodes=[]
        for n in v["nodes"]:
            if type(n) is not dict or set(n)!={"id","label","source_refs"}:raise GraphArtifactError("invalid graph node")
            if type(n["id"]) is not str or not n["id"] or len(n["id"])>200 or n["id"] in ids:raise GraphArtifactError("invalid graph node id")
            if type(n["label"]) is not str or not n["label"] or len(n["label"])>500:raise GraphArtifactError("invalid graph node label")
            if type(n["source_refs"]) is not list or not n["source_refs"] or any(type(x) is not str or not x for x in n["source_refs"]):raise GraphArtifactError("graph node source refs required")
            ids.add(n["id"]);nodes.append({"id":n["id"],"label":n["label"],"source_refs":list(n["source_refs"])})
        edges=[]
        for e in v["edges"]:
            if type(e) is not dict or set(e)!={"source","target","relation","evidence_refs"}:raise GraphArtifactError("invalid graph edge")
            if e["source"] not in ids or e["target"] not in ids:raise GraphArtifactError("graph edge references missing node")
            if type(e["relation"]) is not str or not e["relation"] or len(e["relation"])>200:raise GraphArtifactError("invalid graph relation")
            if type(e["evidence_refs"]) is not list or not e["evidence_refs"] or any(type(x) is not str or not x for x in e["evidence_refs"]):raise GraphArtifactError("graph edge evidence required")
            edges.append({"source":e["source"],"target":e["target"],"relation":e["relation"],"evidence_refs":list(e["evidence_refs"])})
        return {"schema_version":"bie.app.graph-view/1","kind":kind,"run_id":run_id,"artifact_id":artifact_id,
                "nodes":sorted(nodes,key=lambda x:x["id"]),"edges":sorted(edges,key=lambda x:(x["source"],x["target"],x["relation"])),
                "source_bound":True,"product_accepted":False}
