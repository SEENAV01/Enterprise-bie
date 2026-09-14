"""BIE-DIR-HARD-INPUTS-001: canonical envelopes over BIE's existing CAS/catalog.

The catalog is injected; its index persistence is an infrastructure concern.
No alternative artifact ID, hash algorithm or orchestration framework is added.
"""
from dataclasses import asdict
import hashlib
import json

from bie.bie_core.artifact_contracts import (
    ArtifactEnvelope, ArtifactRef, ProducerIdentity, ProvenanceSource, ProvenanceSummary,
)
from bie.infrastructure.artifact_store import ArtifactCatalog, BlobRef
from .contract_validation import acyclic, nonblank


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def fingerprint(value):
    return "sha256:" + hashlib.sha256(canonical(value).encode()).hexdigest()


def parse_json(text):
    def pairs(values):
        result = {}
        for key, value in values:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result
    def constant(_):
        raise ValueError("nonfinite JSON number")
    try:
        value = json.loads(text, object_pairs_hook=pairs, parse_constant=constant)
        canonical(value)  # Reject overflowed exponent literals such as 1e999.
        return value
    except (TypeError, OverflowError, RecursionError) as exc:
        raise ValueError("invalid JSON value") from exc


def fields(value, expected, name):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError(name + " fields mismatch")
    return value


def array(value, name):
    if type(value) is not list:
        raise ValueError(name + " must be a JSON array")
    return value


def reference(value):
    fields(value, ("artifact_id", "artifact_type", "schema_version", "content_hash"), "artifact reference")
    result = ArtifactRef(**value)
    for key in value:
        nonblank(value[key], key)
    result.validate()
    return result


def envelope_from_dict(value):
    fields(value, tuple(ArtifactEnvelope.__dataclass_fields__), "artifact envelope")
    fields(value["producer"], tuple(ProducerIdentity.__dataclass_fields__), "producer")
    provenance = value["provenance_summary"]
    fields(provenance, tuple(ProvenanceSummary.__dataclass_fields__), "provenance")
    if type(value["parent_refs"]) is not list or type(provenance["sources"]) is not list:
        raise ValueError("artifact references/sources must be JSON arrays")
    sources = []
    for item in provenance["sources"]:
        fields(item, tuple(ProvenanceSource.__dataclass_fields__), "provenance source")
        sources.append(ProvenanceSource(**item))
    result = ArtifactEnvelope(**{
        **value, "producer": ProducerIdentity(**value["producer"]),
        "parent_refs": [reference(r) for r in value["parent_refs"]],
        "provenance_summary": ProvenanceSummary(**{**provenance, "sources": sources}),
    })
    result.validate()
    nonblank(result.created_at, "created_at")
    if type(result.metadata) is not dict:
        raise ValueError("metadata must be an object")
    if "requires_review" in result.metadata and type(result.metadata["requires_review"]) is not bool:
        raise ValueError("metadata review flag must be boolean")
    if len({p.artifact_id for p in result.parent_refs}) != len(result.parent_refs):
        raise ValueError("duplicate parent reference")
    return result


class DirectorArtifactIO:
    """Validate CAS bytes, canonical envelope hashes and complete parent refs."""

    def __init__(self, catalog):
        if not isinstance(catalog, ArtifactCatalog):
            raise ValueError("expected existing BIE ArtifactCatalog")
        self.catalog = catalog

    def load(self, ref_or_id):
        aid = ref_or_id.artifact_id if isinstance(ref_or_id, ArtifactRef) else nonblank(ref_or_id, "artifact id")
        record = self.catalog.get_record(aid)
        result = envelope_from_dict(parse_json(self.catalog.read_artifact(aid)))
        if (record.artifact_id != result.artifact_id or record.artifact_type != result.artifact_type
                or record.run_id != result.run_id
                or record.parent_artifact_ids != [p.artifact_id for p in result.parent_refs]):
            raise ValueError("artifact index/envelope mismatch")
        if isinstance(ref_or_id, ArtifactRef) and result.to_ref() != ref_or_id:
            raise ValueError("stale or mismatched artifact reference")
        return result

    def load_graph(self, refs):
        pending = list(refs)
        found = {}
        while pending:
            ref = pending.pop()
            artifact = self.load(ref)
            prior = found.get(artifact.artifact_id)
            if prior is not None:
                if prior.to_ref() != artifact.to_ref():
                    raise ValueError("inconsistent graph reference")
                continue
            found[artifact.artifact_id] = artifact
            pending.extend(artifact.parent_refs)
        acyclic({aid: tuple(p.artifact_id for p in artifact.parent_refs) for aid, artifact in found.items()})
        return found

    def put(self, artifact, stage_id, *, evidence=False):
        # Serialize before storing: mutable lists/dicts in upstream frozen
        # dataclasses are never retained as shared live references.
        artifact = envelope_from_dict(parse_json(canonical(asdict(artifact))))
        self.load_graph(artifact.parent_refs)
        if artifact.artifact_id in self.catalog.records:
            existing = self.load(artifact.to_ref())
            return existing.to_ref()  # Creation timestamp is outside content hash.
        self.catalog.put_artifact(
            artifact.artifact_id, artifact.artifact_type, canonical(asdict(artifact)).encode(),
            artifact.run_id, stage_id, [p.artifact_id for p in artifact.parent_refs],
            evidence=evidence, metadata={"content_hash": artifact.content_hash},
        )
        return self.load(artifact.to_ref()).to_ref()

    def derive(self, artifact_type, run_id, parents, payload, *, stage_id, metadata,
               producer=None, evidence=False):
        parents = tuple(parents)
        graph = self.load_graph(parents)
        sources = {}
        for ref in parents:
            artifact = graph[ref.artifact_id]
            if artifact.run_id != run_id:
                raise ValueError("cross-run parent requires an explicit upstream import")
            for source in artifact.provenance_summary.sources:
                sources[canonical(asdict(source))] = source
        if not sources:
            raise ValueError("derived artifact needs source provenance")
        result = ArtifactEnvelope.create(
            artifact_type, "1.0.0", run_id,
            producer or ProducerIdentity("bie.director.artifact_adapter", "1.0.0", "deterministic"),
            list(parents), ProvenanceSummary([sources[k] for k in sorted(sources)]), metadata, payload,
        )
        return self.put(result, stage_id, evidence=evidence)

    def source_bytes(self, source_ref):
        artifact = self.load(source_ref)
        if artifact.artifact_type != "source.document" or artifact.schema_version != "1.0.0":
            raise ValueError("unsupported source document envelope")
        payload = fields(artifact.payload, ("source_id", "source_sha256", "media_type", "blob"), "source document")
        fields(payload["blob"], tuple(BlobRef.__dataclass_fields__), "source blob")
        blob = BlobRef(**payload["blob"])
        blob.validate()
        if type(blob.size) is not int or blob.size < 1: raise ValueError("source blob must have a positive integer size")
        if payload["source_sha256"] != "sha256:" + blob.digest:
            raise ValueError("source hash/blob mismatch")
        expected = ProvenanceSource(payload["source_id"], {"kind": "whole_source"}, payload["source_sha256"])
        if artifact.parent_refs or artifact.provenance_summary.sources != [expected]:
            raise ValueError("source document provenance mismatch")
        return self.catalog.cas.get_bytes(blob)
