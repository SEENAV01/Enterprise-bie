from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Iterable

from bie.infrastructure.artifact_store import BlobRef

from .contracts import require_identifier


class GraphViewError(ValueError):
    pass


MAX_NODES = 5000
MAX_EDGES = 10000
ALLOWED_KIND = {"concept", "prerequisite"}


@dataclass(frozen=True)
class GraphNode:
    node_id: str
    label: str
    kind: str
    source_refs: tuple[str, ...]


@dataclass(frozen=True)
class GraphEdge:
    edge_id: str
    source: str
    target: str
    relation: str
    source_refs: tuple[str, ...]


def _bounded_text(value: object, fallback: str, *, limit: int = 240) -> str:
    if not isinstance(value, str):
        return fallback
    text = value.strip()
    if not text:
        return fallback
    return text[:limit]


def _refs(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, (list, tuple)):
        raise GraphViewError("graph_source_refs_invalid")
    out = []
    for ref in value:
        out.append(require_identifier(ref, "source_ref", max_length=256))
    return tuple(out)


def _normalize_nodes(raw: object) -> list[GraphNode]:
    rows: Iterable[tuple[str, object]]
    if isinstance(raw, dict):
        rows = raw.items()
    elif isinstance(raw, list):
        rows = ((str(item.get("id", "")), item) for item in raw if isinstance(item, dict))
    else:
        raise GraphViewError("graph_nodes_invalid")

    out: list[GraphNode] = []
    seen: set[str] = set()
    for key, item in rows:
        if not isinstance(item, dict):
            raise GraphViewError("graph_node_invalid")
        node_id = require_identifier(
            str(item.get("id") or item.get("concept_id") or key),
            "node_id",
        )
        if node_id in seen:
            raise GraphViewError("duplicate_graph_node")
        seen.add(node_id)
        label = _bounded_text(
            item.get("label") or item.get("name") or item.get("title"),
            node_id,
        )
        kind = _bounded_text(item.get("kind") or item.get("node_type"), "concept", limit=80)
        refs = _refs(item.get("source_refs") or item.get("evidence_ids") or item.get("provenance"))
        out.append(GraphNode(node_id, label, kind, refs))
        if len(out) > MAX_NODES:
            raise GraphViewError("graph_node_limit")
    return out


def _normalize_edges(raw: object, node_ids: set[str]) -> list[GraphEdge]:
    if raw is None:
        return []
    if not isinstance(raw, list):
        raise GraphViewError("graph_edges_invalid")
    out: list[GraphEdge] = []
    seen: set[str] = set()
    for index, item in enumerate(raw):
        if not isinstance(item, dict):
            raise GraphViewError("graph_edge_invalid")
        source = require_identifier(str(item.get("source", "")), "edge_source")
        target = require_identifier(str(item.get("target", "")), "edge_target")
        if source not in node_ids or target not in node_ids:
            raise GraphViewError("graph_edge_endpoint_missing")
        relation = _bounded_text(item.get("relation") or item.get("type"), "RELATED", limit=80)
        edge_id = require_identifier(str(item.get("id") or f"{source}:{relation}:{target}:{index}"), "edge_id")
        if edge_id in seen:
            raise GraphViewError("duplicate_graph_edge")
        seen.add(edge_id)
        refs = _refs(item.get("source_refs") or item.get("evidence_ids") or item.get("provenance"))
        out.append(GraphEdge(edge_id, source, target, relation, refs))
        if len(out) > MAX_EDGES:
            raise GraphViewError("graph_edge_limit")
    return out


def _unwrap_payload(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise GraphViewError("graph_json_object_required")
    payload = value.get("payload")
    if isinstance(payload, dict):
        return payload
    return value


def _prerequisite_edges(payload: dict[str, object], node_ids: set[str]) -> list[dict[str, object]]:
    existing = payload.get("prerequisite_edges")
    if isinstance(existing, list):
        return existing
    prereqs = payload.get("prerequisites")
    if not isinstance(prereqs, list):
        return []
    edges: list[dict[str, object]] = []
    for index, item in enumerate(prereqs):
        if isinstance(item, dict):
            source = item.get("prerequisite_id") or item.get("source")
            target = item.get("concept_id") or item.get("target")
            refs = item.get("evidence_ids") or item.get("source_refs") or []
        elif isinstance(item, (list, tuple)) and len(item) >= 2:
            source, target, refs = item[0], item[1], []
        else:
            raise GraphViewError("prerequisite_edge_invalid")
        if source is None or target is None:
            raise GraphViewError("prerequisite_edge_invalid")
        edges.append({
            "id": f"prerequisite:{source}:{target}:{index}",
            "source": str(source),
            "target": str(target),
            "relation": "PREREQUISITE",
            "source_refs": refs,
        })
    return edges


class GraphViewService:
    """Read-only graph projection from an actual canonical artifact record."""

    def __init__(self, persistence, cas):
        self.persistence = persistence
        self.cas = cas

    def view(self, run_id: str, artifact_id: str, kind: str) -> dict[str, object]:
        run_id = require_identifier(run_id, "run_id")
        artifact_id = require_identifier(artifact_id, "artifact_id")
        if kind not in ALLOWED_KIND:
            raise GraphViewError("unsupported_graph_kind")

        try:
            record = self.persistence.load_artifact(artifact_id)
        except Exception as exc:
            raise GraphViewError("artifact_not_found") from exc
        if record.run_id != run_id:
            raise GraphViewError("cross_run_artifact")
        try:
            raw = self.cas.get_bytes(
                BlobRef(record.blob_algorithm, record.blob_digest, record.blob_size)
            )
        except Exception as exc:
            raise GraphViewError("artifact_bytes_unavailable") from exc
        try:
            value = json.loads(raw.decode("utf-8"))
        except Exception as exc:
            raise GraphViewError("artifact_json_invalid") from exc

        payload = _unwrap_payload(value)
        graph = payload.get("knowledge_graph")
        if isinstance(graph, dict):
            graph_payload = graph
        else:
            graph_payload = payload

        nodes = _normalize_nodes(graph_payload.get("nodes"))
        node_ids = {node.node_id for node in nodes}
        if kind == "concept":
            edges_raw = graph_payload.get("edges", [])
        else:
            edges_raw = graph_payload.get("prerequisite_edges")
            if edges_raw is None:
                edges_raw = _prerequisite_edges(payload, node_ids)
                if not edges_raw:
                    edges_raw = [
                        edge for edge in graph_payload.get("edges", [])
                        if isinstance(edge, dict)
                        and str(edge.get("relation") or edge.get("type", "")).upper()
                        in {"PREREQUISITE", "DEPENDS_ON"}
                    ]
        edges = _normalize_edges(edges_raw, node_ids)
        return {
            "schema_version": "bie.app.graph-view/1",
            "run_id": run_id,
            "artifact_id": artifact_id,
            "artifact_type": record.artifact_type,
            "kind": kind,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "nodes": [
                {
                    "id": node.node_id,
                    "label": node.label,
                    "kind": node.kind,
                    "source_refs": list(node.source_refs),
                }
                for node in nodes
            ],
            "edges": [
                {
                    "id": edge.edge_id,
                    "source": edge.source,
                    "target": edge.target,
                    "relation": edge.relation,
                    "source_refs": list(edge.source_refs),
                }
                for edge in edges
            ],
            "empty": not nodes,
            "read_only": True,
            "product_accepted": False,
        }
