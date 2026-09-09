from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Iterable
import hashlib
import json
import re
import uuid

SEMVER_RE = re.compile(r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$")


class ArtifactContractError(ValueError):
    pass


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def sha256_json(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class ArtifactRef:
    artifact_id: str
    artifact_type: str
    schema_version: str
    content_hash: str

    def validate(self) -> None:
        if not self.artifact_id:
            raise ArtifactContractError("artifact_id is required")
        if not self.artifact_type:
            raise ArtifactContractError("artifact_type is required")
        if not SEMVER_RE.match(self.schema_version):
            raise ArtifactContractError(f"invalid schema_version: {self.schema_version}")
        if not re.fullmatch(r"[0-9a-f]{64}", self.content_hash):
            raise ArtifactContractError("content_hash must be lowercase SHA-256 hex")


@dataclass(frozen=True)
class ProducerIdentity:
    component: str
    component_version: str
    execution_kind: str
    provider: Optional[str] = None
    model: Optional[str] = None
    tool: Optional[str] = None

    def validate(self) -> None:
        if not self.component or not self.component_version:
            raise ArtifactContractError("producer component and version are required")
        if self.execution_kind not in {"deterministic", "model", "human", "hybrid"}:
            raise ArtifactContractError("invalid execution_kind")


@dataclass(frozen=True)
class ProvenanceSource:
    source_id: str
    locator: Dict[str, Any]
    evidence_hash: Optional[str] = None
    quote_hash: Optional[str] = None

    def validate(self) -> None:
        if not self.source_id:
            raise ArtifactContractError("source_id is required")
        if not isinstance(self.locator, dict) or not self.locator:
            raise ArtifactContractError("provenance locator is required")


@dataclass(frozen=True)
class ProvenanceSummary:
    sources: List[ProvenanceSource] = field(default_factory=list)
    inferred: bool = False
    inference_reason: Optional[str] = None
    confidence: Optional[float] = None

    def validate(self) -> None:
        for src in self.sources:
            src.validate()
        if self.inferred:
            if not self.inference_reason:
                raise ArtifactContractError("inference_reason required when inferred=true")
            if self.confidence is None or not (0.0 <= self.confidence <= 1.0):
                raise ArtifactContractError("confidence 0..1 required for inferred artifacts")


@dataclass(frozen=True)
class RunContext:
    run_id: str
    product: str
    product_version: str
    source_ids: List[str]
    configuration_hash: str
    policy_id: str
    environment_fingerprint: str
    started_at: str
    parent_run_id: Optional[str] = None

    @classmethod
    def new(
        cls,
        product: str,
        product_version: str,
        source_ids: List[str],
        configuration: Dict[str, Any],
        policy_id: str,
        environment_fingerprint: str,
        parent_run_id: Optional[str] = None,
    ) -> "RunContext":
        return cls(
            run_id=str(uuid.uuid4()),
            product=product,
            product_version=product_version,
            source_ids=list(source_ids),
            configuration_hash=sha256_json(configuration),
            policy_id=policy_id,
            environment_fingerprint=environment_fingerprint,
            started_at=utc_now_iso(),
            parent_run_id=parent_run_id,
        )

    def validate(self) -> None:
        try:
            uuid.UUID(self.run_id)
        except Exception as e:
            raise ArtifactContractError("run_id must be UUID") from e
        if not self.product or not SEMVER_RE.match(self.product_version):
            raise ArtifactContractError("valid product and semver product_version required")
        if not re.fullmatch(r"[0-9a-f]{64}", self.configuration_hash):
            raise ArtifactContractError("configuration_hash must be SHA-256 hex")
        if not self.policy_id or not self.environment_fingerprint or not self.started_at:
            raise ArtifactContractError("policy/environment/started_at required")


@dataclass(frozen=True)
class ArtifactEnvelope:
    artifact_id: str
    artifact_type: str
    schema_version: str
    run_id: str
    created_at: str
    producer: ProducerIdentity
    content_hash: str
    parent_refs: List[ArtifactRef]
    provenance_summary: ProvenanceSummary
    metadata: Dict[str, Any]
    payload: Any

    @staticmethod
    def _hash_material(
        artifact_type: str,
        schema_version: str,
        run_id: str,
        producer: ProducerIdentity,
        parent_refs: List[ArtifactRef],
        provenance_summary: ProvenanceSummary,
        metadata: Dict[str, Any],
        payload: Any,
    ) -> Dict[str, Any]:
        return {
            "artifact_type": artifact_type,
            "schema_version": schema_version,
            "run_id": run_id,
            "producer": asdict(producer),
            "parent_refs": [asdict(p) for p in parent_refs],
            "provenance_summary": {
                "sources": [asdict(s) for s in provenance_summary.sources],
                "inferred": provenance_summary.inferred,
                "inference_reason": provenance_summary.inference_reason,
                "confidence": provenance_summary.confidence,
            },
            "metadata": metadata,
            "payload": payload,
        }

    @classmethod
    def create(
        cls,
        artifact_type: str,
        schema_version: str,
        run_id: str,
        producer: ProducerIdentity,
        parent_refs: Optional[List[ArtifactRef]],
        provenance_summary: ProvenanceSummary,
        metadata: Optional[Dict[str, Any]],
        payload: Any,
    ) -> "ArtifactEnvelope":
        parent_refs = list(parent_refs or [])
        metadata = dict(metadata or {})
        material = cls._hash_material(
            artifact_type, schema_version, run_id, producer, parent_refs,
            provenance_summary, metadata, payload
        )
        content_hash = sha256_json(material)
        artifact_id = f"{artifact_type}:{schema_version}:{content_hash[:24]}"
        return cls(
            artifact_id=artifact_id,
            artifact_type=artifact_type,
            schema_version=schema_version,
            run_id=run_id,
            created_at=utc_now_iso(),
            producer=producer,
            content_hash=content_hash,
            parent_refs=parent_refs,
            provenance_summary=provenance_summary,
            metadata=metadata,
            payload=payload,
        )

    def to_ref(self) -> ArtifactRef:
        return ArtifactRef(
            artifact_id=self.artifact_id,
            artifact_type=self.artifact_type,
            schema_version=self.schema_version,
            content_hash=self.content_hash,
        )

    def recompute_content_hash(self) -> str:
        return sha256_json(self._hash_material(
            self.artifact_type,
            self.schema_version,
            self.run_id,
            self.producer,
            self.parent_refs,
            self.provenance_summary,
            self.metadata,
            self.payload,
        ))

    def validate(self, source_root_types: Optional[Iterable[str]] = None) -> None:
        roots = set(source_root_types or {"source.document", "source.block", "source.asset"})
        if not self.artifact_type:
            raise ArtifactContractError("artifact_type is required")
        if not SEMVER_RE.match(self.schema_version):
            raise ArtifactContractError("schema_version must be semver")
        try:
            uuid.UUID(self.run_id)
        except Exception as e:
            raise ArtifactContractError("run_id must be UUID") from e
        self.producer.validate()
        self.provenance_summary.validate()
        for ref in self.parent_refs:
            ref.validate()
        if self.artifact_type not in roots and not self.parent_refs:
            raise ArtifactContractError("non-source artifact requires parent_refs")
        actual = self.recompute_content_hash()
        if actual != self.content_hash:
            raise ArtifactContractError("content hash mismatch")
        expected_id = f"{self.artifact_type}:{self.schema_version}:{actual[:24]}"
        if self.artifact_id != expected_id:
            raise ArtifactContractError("artifact_id does not match canonical content")


class LineageGraph:
    def __init__(self, artifacts: Iterable[ArtifactEnvelope]):
        self.by_id = {a.artifact_id: a for a in artifacts}

    def validate(self) -> None:
        for artifact in self.by_id.values():
            artifact.validate()
            for ref in artifact.parent_refs:
                parent = self.by_id.get(ref.artifact_id)
                if parent is None:
                    raise ArtifactContractError(
                        f"missing parent artifact {ref.artifact_id} for {artifact.artifact_id}"
                    )
                if parent.content_hash != ref.content_hash:
                    raise ArtifactContractError("parent reference hash mismatch")
        self._assert_acyclic()

    def _assert_acyclic(self) -> None:
        visiting, visited = set(), set()
        def dfs(aid: str):
            if aid in visiting:
                raise ArtifactContractError("cyclic lineage detected")
            if aid in visited:
                return
            visiting.add(aid)
            for ref in self.by_id[aid].parent_refs:
                dfs(ref.artifact_id)
            visiting.remove(aid)
            visited.add(aid)
        for aid in self.by_id:
            dfs(aid)

    def trace_to_sources(self, artifact_id: str) -> List[ArtifactEnvelope]:
        if artifact_id not in self.by_id:
            raise ArtifactContractError("artifact not found")
        sources, seen = [], set()
        def walk(a: ArtifactEnvelope):
            if a.artifact_id in seen:
                return
            seen.add(a.artifact_id)
            if not a.parent_refs:
                sources.append(a)
                return
            for ref in a.parent_refs:
                walk(self.by_id[ref.artifact_id])
        walk(self.by_id[artifact_id])
        return sources
