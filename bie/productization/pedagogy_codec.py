"""Durable canonical Director codecs over the existing producer SQLite/CAS.

This codec expands verified upstream evidence to its actual DI source blocks.
It never executes Director or substitutes model text for a native contract.
"""
from dataclasses import asdict, replace

from bie.bie_core.artifact_contracts import ArtifactRef
from bie.infrastructure.artifact_store import ArtifactCatalog, ArtifactRecord, BlobRef
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.director.director_artifacts import DirectorArtifactIO, envelope_from_dict
from bie.director.director_inputs import (
    publish_source_catalog, load_source_catalog, publish_reasoning, publish_pedagogy,
    load_director_inputs, _decision, _pedagogy, _binding,
)
from bie.director.qa_contract import SourceCatalog, SourcePage, SourcePassage
from bie.director.source_grounding_qa import SourceBytes
from bie.pedagogy.learning_objective_generator import LearningObjective
from .contracts import require, canonical, digest, strict_json, sha


class ProducerArtifactCatalog(ArtifactCatalog):
    """Rehydrate native envelope records from the SAME canonical run database."""

    def __init__(self, service, run_id):
        super().__init__(service.cas)
        self.service, self.run_id = service, run_id
        pending = {}
        for aid in service.persistence.artifacts_for_run(run_id):
            row = service.persistence.load_artifact(aid)
            if row.metadata.get("producer_codec") == "director-input-v1":
                pending[aid] = self.convert(row)
        require(len(pending) <= 1000, "director_codec_budget")
        while pending:
            ready = [aid for aid, row in pending.items()
                     if set(row.parent_artifact_ids) <= self.records.keys()]
            require(ready, "director_codec_ancestry")
            for aid in sorted(ready):
                super().register(pending.pop(aid))

    @staticmethod
    def convert(row):
        return ArtifactRecord(row.artifact_id, row.artifact_type,
            BlobRef(row.blob_algorithm, row.blob_digest, row.blob_size),
            row.run_id, row.stage_id, row.parent_artifact_ids, row.evidence, row.metadata)

    def get_record(self, aid):
        row = self.service.persistence.load_artifact(aid)
        require(row.run_id == self.run_id and
                row.metadata.get("producer_codec") == "director-input-v1", "foreign_director_artifact")
        record = self.convert(row)
        require(self.records.get(aid) == record, "director_codec_index_mismatch")
        self.cas.get_bytes(record.blob)
        return record

    def register(self, record):
        self.service.write_guard()
        require(record.run_id == self.run_id, "foreign_director_artifact")
        # Canonical ArtifactCatalog validates CAS and parents before publication.
        super().register(record)
        metadata = dict(record.metadata, privacy="PRIVATE",
                        producer_codec="director-input-v1", profile=self.service.profile)
        durable = PersistedArtifactRecord(record.artifact_id, record.artifact_type,
            record.blob.algorithm, record.blob.digest, record.blob.size, record.run_id,
            record.stage_id, record.evidence, metadata, record.parent_artifact_ids)
        self.service.write_guard()
        self.service.persistence.register_artifact(durable)
        self.records[record.artifact_id] = self.convert(durable)


class ProducerDirectorIO(DirectorArtifactIO):
    def __init__(self, service, run_id, pedagogy_metadata=None):
        super().__init__(ProducerArtifactCatalog(service, run_id))
        self.pedagogy_metadata = pedagogy_metadata

    def derive(self, artifact_type, run_id, parents, payload, *, stage_id, metadata,
               producer=None, evidence=False):
        if artifact_type == "pedagogy.plan" and self.pedagogy_metadata is not None:
            metadata = dict(metadata, **self.pedagogy_metadata)
        return super().derive(artifact_type, run_id, parents, payload, stage_id=stage_id,
                             metadata=metadata, producer=producer, evidence=evidence)


def source_catalog(document, source_id):
    """Serialize actual extracted blocks; offsets are in the extracted page text."""
    pages, passages = [], []
    blocks = sorted(document["blocks"], key=lambda b: (b["physical_page"], b["reading_order"]))
    for number in sorted({b["physical_page"] for b in blocks}):
        selected = [b for b in blocks if b["physical_page"] == number]
        text = "\n".join(b["text"] for b in selected)
        page = SourcePage("page-" + digest(dict(source=source_id, page=number)),
            source_id, "sha256:" + document["source_sha256"], number, text,
            "document.structured:" + document["runtime_identity"])
        pages.append(page)
        offset = 0
        for block in selected:
            end = offset + len(block["text"])
            passages.append(SourcePassage(block["anchor_id"], page.page_id,
                page.fingerprint(), block["region_id"], offset, end, block["text"]))
            offset = end + 1
    return SourceCatalog(tuple(pages), tuple(passages))


def source_decisions(reasoning, prerequisite, math, artifact_ids, bindings):
    """Preserve decision values/uncertainty; expand artifact refs to source refs.

    The exact unmodified upstream decision_set remains the admitted input. This
    versioned representation records its hash in the Pedagogy envelope metadata.
    """
    scopes = {
        artifact_ids["knowledge"]: reasoning["source_anchor_ids"],
        artifact_ids["prerequisite"]: sorted({a for e in prerequisite["edges"] for a in e["anchor_ids"]})
            or reasoning["source_anchor_ids"],
        artifact_ids["math"]: [b["anchor_id"] for b in math["source_inventory"]],
    }
    result = []
    for raw in reasoning["decisions"]:
        decision = _decision(raw)
        evidence = {}
        for ref in decision.evidence_refs:
            require(ref.artifact_id in scopes, "foreign_reasoning_evidence")
            for anchor in scopes[ref.artifact_id]:
                require(anchor in bindings, "foreign_source_anchor")
                aid = bindings[anchor].artifact_id
                candidate = replace(ref, artifact_id=aid,
                    note="Verified upstream artifact expanded to canonical DI source block")
                # Duplicate source support cannot increase evidence strength.
                if aid in evidence:
                    candidate = replace(candidate, strength=min(candidate.strength, evidence[aid].strength))
                evidence[aid] = candidate
        require(evidence, "reasoning_missing_source_evidence")
        result.append(replace(decision, evidence_refs=tuple(evidence[k] for k in sorted(evidence))))
    return tuple(result)


def native_objects(components):
    plan = _pedagogy(components["plan"])
    objectives = tuple(LearningObjective(**dict(o, evidence_ids=tuple(o["evidence_ids"])))
                       for o in components["objectives"])
    bindings = tuple(_binding(b) for b in components["bindings"])
    return plan, objectives, bindings


def publish(service, run_id, document, prerequisite, math, reasoning, ids, components):
    metadata = dict(producer_schema=components["schema"],
                    producer_profile=service.profile, private=True,
                    technical_evidence="TECHNICAL_SOURCE_DERIVED", accepted=False,
                    upstream=components["upstream"], instructional=components)
    io = ProducerDirectorIO(service, run_id, metadata)
    source_record = service.record(run_id, run_id + "-source")
    raw = service.cas.get_bytes(BlobRef(source_record.blob_algorithm,
                                      source_record.blob_digest, source_record.blob_size))
    require(sha(raw) == document["source_sha256"], "source_hash_mismatch")
    catalog = source_catalog(document, components["source_id"])
    source_ref = publish_source_catalog(io, run_id, catalog,
        (SourceBytes(components["source_id"], raw, "application/pdf"),))
    _, _, _, evidence_bindings, _ = load_source_catalog(io, source_ref)
    decisions = source_decisions(reasoning, prerequisite, math, ids, evidence_bindings)
    reasoning_ref = publish_reasoning(io, run_id, source_ref, decisions)
    plan, objectives, bindings = native_objects(components)
    pedagogy_ref = publish_pedagogy(io, run_id, source_ref, reasoning_ref, plan, objectives, bindings)
    inputs = load_director_inputs(io, reasoning_ref, pedagogy_ref,
        lesson_id=components["plan"]["lesson_ids"][0], title="Bounded instructional plan",
        language="en", run_id=run_id)
    require(inputs.review_reasons, "pedagogy_review_removed")
    return asdict(io.load(pedagogy_ref))


def validate(service, run_id, value, document, prerequisite, math, reasoning, ids, components):
    envelope = envelope_from_dict(value)
    require(envelope.run_id == run_id and envelope.artifact_type == "pedagogy.plan" and
            envelope.schema_version == "1.0.0", "pedagogy_envelope_contract")
    require(envelope.metadata == dict(requires_review=True,
        producer_schema=components["schema"], producer_profile=service.profile,
        private=True, technical_evidence="TECHNICAL_SOURCE_DERIVED", accepted=False,
        upstream=components["upstream"], instructional=components), "pedagogy_intent_mismatch")
    io = ProducerDirectorIO(service, run_id)
    require(io.load(envelope.to_ref()) == envelope, "pedagogy_catalog_mismatch")
    rp = ArtifactRef(**envelope.payload["reasoning_ref"])
    sp = ArtifactRef(**envelope.payload["source_catalog_ref"])
    _, catalog, _, bindings, _ = load_source_catalog(io, sp)
    require(catalog == source_catalog(document, components["source_id"]), "source_catalog_mismatch")
    expected_decisions = source_decisions(reasoning, prerequisite, math, ids, bindings)
    require(canonical(io.load(rp).payload["decisions"]) == canonical([asdict(d) for d in expected_decisions]),
            "reasoning_projection_mismatch")
    expected = dict(source_catalog_ref=asdict(sp), reasoning_ref=asdict(rp),
        plan=components["plan"], objectives=components["objectives"], bindings=components["bindings"])
    require(canonical(envelope.payload) == canonical(expected), "invalid_pedagogy_candidate")
    return load_director_inputs(io, rp, envelope.to_ref(),
        lesson_id=components["plan"]["lesson_ids"][0], title="Bounded instructional plan",
        language="en", run_id=run_id)
