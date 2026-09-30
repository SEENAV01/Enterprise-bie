"""Immutable dataset snapshots and lineage (BIE-EVAL-REG-002)."""
from __future__ import annotations
from dataclasses import dataclass
from .models import (BenchmarkCase, BenchmarkError, canonical_json, digest, digest_string,
                     exact_fields, ident, strict_loads, version_tuple)
from .registry import Registry

@dataclass(frozen=True)
class Snapshot:
    body_json: str
    sha256: str

    def __post_init__(self) -> None:
        digest_string(self.sha256)
        body = strict_loads(self.body_json)
        exact_fields(body, {"schema_version", "dataset_id", "version", "parent_sha256", "cases"})
        if body["schema_version"] != "1.0.0" or type(body["cases"]) is not list or not body["cases"]:
            raise BenchmarkError("INVALID_SNAPSHOT")
        ident(body["dataset_id"])
        version_tuple(body["version"])
        if body["parent_sha256"] is not None:
            digest_string(body["parent_sha256"])
        cases = tuple(BenchmarkCase.from_dict(c) for c in body["cases"])
        ids = [c.case_id for c in cases]
        if ids != sorted(set(ids)):
            raise BenchmarkError("SNAPSHOT_CASE_ORDER_OR_DUPLICATES")
        if canonical_json(body) != self.body_json or digest(body) != self.sha256:
            raise BenchmarkError("SNAPSHOT_TAMPERED")

    @property
    def body(self) -> dict:
        return strict_loads(self.body_json)

    @property
    def cases(self) -> tuple[BenchmarkCase, ...]:
        return tuple(BenchmarkCase.from_dict(c) for c in self.body["cases"])

    def public_manifest(self) -> dict:
        b = self.body
        return {"dataset_id": b["dataset_id"], "version": b["version"],
                "sha256": self.sha256, "parent_sha256": b["parent_sha256"],
                "case_count": len(b["cases"]), "release_authorized": False}


class VersionStore:
    def __init__(self, registry: Registry):
        self.registry = registry
        with registry.transaction():
            registry.connection.execute("""CREATE TABLE IF NOT EXISTS snapshots (
                dataset_id TEXT NOT NULL, version TEXT NOT NULL, sha256 TEXT NOT NULL UNIQUE,
                body TEXT NOT NULL, PRIMARY KEY(dataset_id,version))""")

    def create(self, dataset_id: str, version: str, case_ids: list[str],
               *, parent_sha256: str | None = None) -> Snapshot:
        ident(dataset_id)
        ver = version_tuple(version)
        if type(case_ids) is not list or not case_ids or len(case_ids) != len(set(case_ids)):
            raise BenchmarkError("INVALID_SNAPSHOT_CASE_IDS")
        for case_id in case_ids:
            ident(case_id)
        with self.registry.transaction():
            existing = self.registry.connection.execute(
                "SELECT version,sha256 FROM snapshots WHERE dataset_id=?", (dataset_id,)).fetchall()
            if existing:
                latest = max(existing, key=lambda r: version_tuple(r["version"]))
                if ver <= version_tuple(latest["version"]):
                    raise BenchmarkError("VERSION_NOT_INCREASING")
                if parent_sha256 != latest["sha256"]:
                    raise BenchmarkError("PARENT_MISMATCH")
                self.get(dataset_id, latest["version"])  # fail on tampered predecessor
            elif parent_sha256 is not None:
                raise BenchmarkError("UNEXPECTED_PARENT")
            body = {"schema_version": "1.0.0", "dataset_id": dataset_id, "version": version,
                    "parent_sha256": parent_sha256,
                    "cases": [self.registry.get_case(i).to_dict() for i in sorted(case_ids)]}
            snapshot = Snapshot(canonical_json(body), digest(body))
            self.registry.connection.execute("INSERT INTO snapshots VALUES (?,?,?,?)",
                (dataset_id, version, snapshot.sha256, snapshot.body_json))
            self.registry._event("CREATE_SNAPSHOT", snapshot.public_manifest())
        return snapshot

    def get(self, dataset_id: str, version: str) -> Snapshot:
        ident(dataset_id)
        version_tuple(version)
        row = self.registry.connection.execute(
            "SELECT * FROM snapshots WHERE dataset_id=? AND version=?", (dataset_id, version)).fetchone()
        if row is None:
            raise BenchmarkError("SNAPSHOT_NOT_FOUND")
        snapshot = Snapshot(row["body"], row["sha256"])
        if snapshot.body["dataset_id"] != dataset_id or snapshot.body["version"] != version:
            raise BenchmarkError("SNAPSHOT_IDENTITY_TAMPERED")
        return snapshot

    def verify_lineage(self, snapshot: Snapshot) -> tuple[str, ...]:
        seen: set[str] = set()
        lineage: list[str] = []
        current = snapshot
        while True:
            if current.sha256 in seen:
                raise BenchmarkError("LINEAGE_CYCLE")
            seen.add(current.sha256)
            lineage.append(current.sha256)
            parent = current.body["parent_sha256"]
            if parent is None:
                return tuple(lineage)
            row = self.registry.connection.execute("SELECT * FROM snapshots WHERE sha256=?", (parent,)).fetchone()
            if row is None:
                raise BenchmarkError("PARENT_NOT_FOUND")
            previous = Snapshot(row["body"], row["sha256"])
            if (previous.body["dataset_id"] != current.body["dataset_id"] or
                version_tuple(previous.body["version"]) >= version_tuple(current.body["version"])):
                raise BenchmarkError("INVALID_LINEAGE")
            current = previous


def snapshot_diff(before: Snapshot, after: Snapshot) -> dict:
    if before.body["dataset_id"] != after.body["dataset_id"]:
        raise BenchmarkError("DIFFERENT_DATASETS")
    a = {c.case_id: c.content_sha256 for c in before.cases}
    b = {c.case_id: c.content_sha256 for c in after.cases}
    return {"added": sorted(b.keys() - a.keys()), "removed": sorted(a.keys() - b.keys()),
            "changed": sorted(k for k in a.keys() & b.keys() if a[k] != b[k]),
            "before_sha256": before.sha256, "after_sha256": after.sha256}
