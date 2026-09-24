"""H7: durable segment-level cache lifecycle over canonical BIE CAS/lease APIs.

This cache is an AUDIO hardening adapter, not another orchestrator. It reuses the
existing FileSystemCAS, SQLiteIdempotencyStore and DirectorLeaseStore contracts.
Cache identity is content/configuration based and intentionally excludes run/job
IDs so byte-identical governed segment work may be reused across runs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, is_dataclass
from pathlib import Path
import hashlib
import json
import os
import re
import stat
import time
import uuid

from bie.infrastructure.artifact_store import BlobRef, FileSystemCAS, ArtifactStoreError
from bie.infrastructure.idempotency_store import SQLiteIdempotencyStore, IdempotencyError
from bie.director.director_durable_recovery import DirectorLeaseStore, RecoveryError, FencedLease

from .acoustic_contract import canonical, fields, plain
from .common import AudioError, fingerprint, integer, text
from .durable_store import private_root
from .pipeline_profile import validate_profile
from .pipeline_stems import canonicalize_stem_specs, stems_fingerprint

IDENTITY_SCHEMA = "bie.audio.segment-cache-identity/1"
ENTRY_SCHEMA = "bie.audio.segment-cache-entry/1"
CACHE_KEY_PREFIX = "AUDIO:SEGMENT-CACHE:"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")

RECEIPT_SCHEMA = "bie.audio.segment-cache-receipt/1"

def build_segment_receipt(identity, speech_bytes, *, provider_receipt_fingerprint):
    identity = validate_segment_identity(plain(identity))
    if type(speech_bytes) is not bytes or not speech_bytes:
        raise AudioError("SEGMENT_CACHE_SPEECH_BUDGET")
    if type(provider_receipt_fingerprint) is not str or not provider_receipt_fingerprint.startswith("sha256:") or not HEX64.fullmatch(provider_receipt_fingerprint[7:]):
        raise AudioError("SEGMENT_CACHE_PROVIDER_RECEIPT")
    value = {
        "schema_version": RECEIPT_SCHEMA,
        "identity_fingerprint": identity["fingerprint"],
        "media_sha256": hashlib.sha256(speech_bytes).hexdigest(),
        "media_bytes": len(speech_bytes),
        "provider_receipt_fingerprint": provider_receipt_fingerprint,
        "product_accepted": False,
    }
    value["fingerprint"] = fingerprint(value)
    return value

def validate_segment_receipt(value, identity, speech_bytes):
    identity = validate_segment_identity(plain(identity))
    fields(value, ("schema_version", "identity_fingerprint", "media_sha256", "media_bytes",
                   "provider_receipt_fingerprint", "product_accepted", "fingerprint"),
           "SEGMENT_CACHE_RECEIPT_FIELDS")
    if value["schema_version"] != RECEIPT_SCHEMA or value["identity_fingerprint"] != identity["fingerprint"]:
        raise AudioError("SEGMENT_CACHE_RECEIPT_BINDING")
    if value["product_accepted"] is not False:
        raise AudioError("SEGMENT_CACHE_RECEIPT_ACCEPTANCE")
    if type(value["media_bytes"]) is not int or value["media_bytes"] != len(speech_bytes):
        raise AudioError("SEGMENT_CACHE_RECEIPT_SIZE")
    if type(value["media_sha256"]) is not str or not HEX64.fullmatch(value["media_sha256"]) or value["media_sha256"] != hashlib.sha256(speech_bytes).hexdigest():
        raise AudioError("SEGMENT_CACHE_RECEIPT_MEDIA")
    pr=value["provider_receipt_fingerprint"]
    if type(pr) is not str or not pr.startswith("sha256:") or not HEX64.fullmatch(pr[7:]):
        raise AudioError("SEGMENT_CACHE_PROVIDER_RECEIPT")
    if value["fingerprint"] != fingerprint({k:v for k,v in value.items() if k!="fingerprint"}):
        raise AudioError("SEGMENT_CACHE_RECEIPT_DRIFT")
    return value


@dataclass(frozen=True)
class SegmentCachePolicy:
    revision: str = "audio-h7-segment-cache-v1"
    lease_ttl_seconds: int = 30
    max_attempts: int = 3
    max_segment_bytes: int = 32_000_000
    max_receipt_bytes: int = 2_000_000
    max_cache_bytes: int = 2_000_000_000
    def __post_init__(self):
        text(self.revision, "segment cache revision", 160)
        for name, lo, hi in (
            ("lease_ttl_seconds", 3, 3600),
            ("max_attempts", 1, 10),
            ("max_segment_bytes", 1024, 100_000_000),
            ("max_receipt_bytes", 128, 8_000_000),
            ("max_cache_bytes", 1_000_000, 20_000_000_000),
        ):
            integer(getattr(self, name), name, lo, hi)
        if self.max_segment_bytes + self.max_receipt_bytes > self.max_cache_bytes:
            raise AudioError("SEGMENT_CACHE_POLICY_BUDGET")


@dataclass(frozen=True)
class SegmentTicket:
    lease: FencedLease
    claimed_result_ref: str | None


def _segment_plain(segment):
    value = plain(asdict(segment)) if is_dataclass(segment) else plain(segment)
    required = (
        "segment_id", "utterance_id", "utterance_fingerprint", "script_fingerprint",
        "scene_id", "persona_id", "language", "start", "end", "display_text",
        "spans", "objective_ids", "pause_after_ms", "pause_refs",
    )
    fields(value, required, "SEGMENT_CACHE_SEGMENT_FIELDS")
    text(value["segment_id"], "segment id", 2048)
    text(value["utterance_id"], "utterance id", 2048)
    text(value["scene_id"], "scene id", 2048)
    text(value["persona_id"], "persona id", 2048)
    if type(value["spans"]) is not list or not value["spans"]:
        raise AudioError("SEGMENT_CACHE_SOURCE_REQUIRED")
    refs = []
    for span in value["spans"]:
        if type(span) is not dict or type(span.get("source_refs")) is not list or not span["source_refs"]:
            raise AudioError("SEGMENT_CACHE_SOURCE_REQUIRED")
        refs.extend(span["source_refs"])
    return value, sorted(set(refs))


def _build_segment_identity_validated(segment, *, profile, preparation_profile, mix_stems_fingerprint, policy):
    segment, source_refs = _segment_plain(segment)
    value = {
        "schema_version": IDENTITY_SCHEMA,
        "segment_id": segment["segment_id"],
        "segment_fingerprint": fingerprint(segment),
        "utterance_fingerprint": segment["utterance_fingerprint"],
        "script_fingerprint": segment["script_fingerprint"],
        "source_refs": source_refs,
        "preparation_profile": preparation_profile,
        "profile_fingerprint": profile["fingerprint"],
        "provider_runtime_fingerprint": profile["provider_runtime_fingerprint"],
        "catalog_fingerprint": profile["catalog_fingerprint"],
        "mix_stems_fingerprint": mix_stems_fingerprint,
        "policy_revision": policy.revision,
    }
    value["fingerprint"] = fingerprint(value)
    return value

def build_segment_identity(segment, *, profile, preparation_profile, mix_stems=None,
                           policy=SegmentCachePolicy()):
    """Create a cross-run immutable identity for one prepared speech segment."""
    if type(policy) is not SegmentCachePolicy:
        raise AudioError("SEGMENT_CACHE_POLICY_TYPE")
    profile = plain(profile)
    validate_profile(profile)
    if preparation_profile not in ("batch001-144", "batch001-204"):
        raise AudioError("SEGMENT_CACHE_PREPARATION_PROFILE")
    stems = canonicalize_stem_specs([] if mix_stems is None else mix_stems)
    return _build_segment_identity_validated(segment, profile=profile, preparation_profile=preparation_profile,
                                             mix_stems_fingerprint=stems_fingerprint(stems), policy=policy)


def validate_segment_identity(value):
    fields(value, (
        "schema_version", "segment_id", "segment_fingerprint", "utterance_fingerprint",
        "script_fingerprint", "source_refs", "preparation_profile", "profile_fingerprint",
        "provider_runtime_fingerprint", "catalog_fingerprint", "mix_stems_fingerprint",
        "policy_revision", "fingerprint",
    ), "SEGMENT_CACHE_IDENTITY_FIELDS")
    if value["schema_version"] != IDENTITY_SCHEMA:
        raise AudioError("SEGMENT_CACHE_IDENTITY_VERSION")
    for k in ("segment_id", "preparation_profile", "policy_revision"):
        text(value[k], k, 2048)
    if type(value["source_refs"]) is not list or not value["source_refs"] or value["source_refs"] != sorted(set(value["source_refs"])):
        raise AudioError("SEGMENT_CACHE_SOURCE_REFS")
    for ref in value["source_refs"]:
        text(ref, "source reference", 2048)
    for k in ("segment_fingerprint", "utterance_fingerprint", "script_fingerprint",
              "profile_fingerprint", "provider_runtime_fingerprint", "catalog_fingerprint",
              "mix_stems_fingerprint", "fingerprint"):
        if type(value[k]) is not str or not value[k].startswith("sha256:") or not HEX64.fullmatch(value[k][7:]):
            raise AudioError("SEGMENT_CACHE_FINGERPRINT")
    body = {k: v for k, v in value.items() if k != "fingerprint"}
    if value["fingerprint"] != fingerprint(body):
        raise AudioError("SEGMENT_CACHE_IDENTITY_DRIFT")
    return value


def segment_cache_key(identity):
    validate_segment_identity(identity)
    return CACHE_KEY_PREFIX + identity["fingerprint"][7:]


def _blob(row):
    if type(row) is not dict or set(row) != set(BlobRef.__dataclass_fields__):
        raise AudioError("SEGMENT_CACHE_BLOB_FIELDS")
    ref = BlobRef(**row)
    ref.validate()
    return ref


def _entry(identity, speech_ref, receipt_ref):
    value = {
        "schema_version": ENTRY_SCHEMA,
        "identity_fingerprint": identity["fingerprint"],
        "speech": asdict(speech_ref),
        "receipt": asdict(receipt_ref),
    }
    value["fingerprint"] = fingerprint(value)
    return value


def _parse_entry(text_value):
    try:
        value = json.loads(text_value)
    except (TypeError, ValueError) as exc:
        raise AudioError("SEGMENT_CACHE_ENTRY_JSON") from exc
    fields(value, ("schema_version", "identity_fingerprint", "speech", "receipt", "fingerprint"),
           "SEGMENT_CACHE_ENTRY_FIELDS")
    if value["schema_version"] != ENTRY_SCHEMA:
        raise AudioError("SEGMENT_CACHE_ENTRY_VERSION")
    _blob(value["speech"]); _blob(value["receipt"])
    if value["fingerprint"] != fingerprint({k: v for k, v in value.items() if k != "fingerprint"}):
        raise AudioError("SEGMENT_CACHE_ENTRY_DRIFT")
    return value


class SegmentCacheStore:
    """Durable segment cache using canonical CAS + lease/idempotency stores."""
    def __init__(self, root, *, policy=SegmentCachePolicy()):
        if type(policy) is not SegmentCachePolicy:
            raise AudioError("SEGMENT_CACHE_POLICY_TYPE")
        self.root = private_root(root)
        self.policy = policy
        self.cas = FileSystemCAS(self.root / "cas")
        self.db_path = self.root / "segment-cache.sqlite"

    def _stores(self):
        leases = DirectorLeaseStore(self.db_path)
        claims = SQLiteIdempotencyStore(str(self.db_path))
        return leases, claims

    def acquire(self, identity, *, now=None):
        identity = validate_segment_identity(plain(identity)); key = segment_cache_key(identity)
        current = time.time() if now is None else now
        leases, claims = self._stores()
        try:
            try: prior = leases.get(key)
            except RecoveryError: prior = None
            if prior and prior.state != "COMPLETED" and prior.expires_at <= current and prior.epoch >= self.policy.max_attempts:
                raise AudioError("SEGMENT_CACHE_ATTEMPTS_EXHAUSTED")
            lease = leases.acquire(key, identity["fingerprint"], "audio-segment:" + uuid.uuid4().hex,
                                   now=now, ttl_seconds=self.policy.lease_ttl_seconds)
            claim = claims.claim(key, identity["fingerprint"], lease.owner)
            if claim.state == "COMPLETED":
                if lease.state == "COMPLETED" and lease.result_ref != claim.result_ref:
                    raise AudioError("SEGMENT_CACHE_COMPLETION_CONFLICT")
                return SegmentTicket(lease, claim.result_ref)
            if lease.state == "COMPLETED":
                raise AudioError("SEGMENT_CACHE_COMPLETION_CONFLICT")
            if claim.owner != lease.owner:
                leases.reclaim_idempotency(claims, lease, lease.owner, now=now)
            return SegmentTicket(lease, None)
        finally:
            claims.close(); leases.close()

    def heartbeat(self, ticket, *, now=None):
        leases, claims = self._stores()
        try:
            updated = leases.heartbeat(ticket.lease, now=now, ttl_seconds=self.policy.lease_ttl_seconds)
            return SegmentTicket(updated, ticket.claimed_result_ref)
        finally:
            claims.close(); leases.close()

    def put(self, ticket, identity, speech_bytes, receipt_bytes, *, now=None):
        identity = validate_segment_identity(plain(identity)); key = segment_cache_key(identity)
        if ticket.lease.key != key or ticket.lease.fingerprint != identity["fingerprint"]:
            raise AudioError("SEGMENT_CACHE_TICKET_BINDING")
        if type(speech_bytes) is not bytes or not 0 < len(speech_bytes) <= self.policy.max_segment_bytes:
            raise AudioError("SEGMENT_CACHE_SPEECH_BUDGET")
        if type(receipt_bytes) is not bytes or not 0 < len(receipt_bytes) <= self.policy.max_receipt_bytes:
            raise AudioError("SEGMENT_CACHE_RECEIPT_BUDGET")
        try:
            receipt_value=json.loads(receipt_bytes.decode("utf-8"))
        except (UnicodeDecodeError, ValueError) as exc:
            raise AudioError("SEGMENT_CACHE_RECEIPT_JSON") from exc
        validate_segment_receipt(receipt_value, identity, speech_bytes)
        # Dedicated cache root: reserve against actual CAS file bytes before writes.
        total = sum(p.stat().st_size for p in (self.root / "cas").rglob("*") if p.is_file())
        if total + len(speech_bytes) + len(receipt_bytes) > self.policy.max_cache_bytes:
            raise AudioError("SEGMENT_CACHE_TOTAL_BUDGET")
        speech_ref = self.cas.put_bytes(speech_bytes)
        receipt_ref = self.cas.put_bytes(receipt_bytes)
        entry = _entry(identity, speech_ref, receipt_ref)
        encoded = canonical(entry).decode("utf-8")
        leases, claims = self._stores()
        try:
            current = leases.get(key)
            if current.state != "COMPLETED":
                leases.assert_active(ticket.lease, now=now)
            elif current != ticket.lease or current.result_ref != encoded:
                raise AudioError("SEGMENT_CACHE_FOREIGN_COMPLETION")
            # Re-read canonical CAS content before publishing completion.
            if self.cas.get_bytes(speech_ref) != speech_bytes or self.cas.get_bytes(receipt_ref) != receipt_bytes:
                raise AudioError("SEGMENT_CACHE_CAS_VERIFY")
            claims.complete(key, ticket.lease.owner, encoded)
            if current.state != "COMPLETED":
                leases.complete(ticket.lease, encoded, now=now)
            return self.get(identity)
        finally:
            claims.close(); leases.close()

    def get(self, identity):
        identity = validate_segment_identity(plain(identity)); key = segment_cache_key(identity)
        leases, claims = self._stores()
        try:
            try: claim = claims.get(key)
            except IdempotencyError as exc: raise AudioError("SEGMENT_CACHE_MISS") from exc
            if claim.state != "COMPLETED" or not claim.result_ref:
                raise AudioError("SEGMENT_CACHE_INCOMPLETE")
            entry = _parse_entry(claim.result_ref)
            if entry["identity_fingerprint"] != identity["fingerprint"]:
                raise AudioError("SEGMENT_CACHE_IDENTITY_MISMATCH")
            speech_ref, receipt_ref = _blob(entry["speech"]), _blob(entry["receipt"])
            if speech_ref.size > self.policy.max_segment_bytes or receipt_ref.size > self.policy.max_receipt_bytes:
                raise AudioError("SEGMENT_CACHE_STORED_BUDGET")
            speech = self.cas.get_bytes(speech_ref); receipt = self.cas.get_bytes(receipt_ref)
            try: receipt_value=json.loads(receipt.decode("utf-8"))
            except (UnicodeDecodeError, ValueError) as exc: raise AudioError("SEGMENT_CACHE_RECEIPT_JSON") from exc
            validate_segment_receipt(receipt_value, identity, speech)
            lease = leases.get(key)
            if lease.state != "COMPLETED" or lease.result_ref != claim.result_ref:
                raise AudioError("SEGMENT_CACHE_INDEX_DISAGREEMENT")
            return {"identity": identity, "entry": entry, "speech_bytes": speech, "receipt_bytes": receipt,
                    "cache_key": key, "scope": "SEGMENT_CACHE_REUSE_NOT_ACOUSTIC_ACCEPTANCE",
                    "product_accepted": False}
        except ArtifactStoreError as exc:
            raise AudioError("SEGMENT_CACHE_CAS_CORRUPT") from exc
        finally:
            claims.close(); leases.close()

    def has(self, identity):
        try: self.get(identity); return True
        except AudioError as exc:
            if exc.code in {"SEGMENT_CACHE_MISS", "SEGMENT_CACHE_INCOMPLETE"}: return False
            raise

    def referenced_digests(self):
        """Return completed segment-cache CAS digests; dedicated-root inspection only."""
        leases, claims = self._stores(); refs = set()
        try:
            rows = claims.db.execute("SELECT result_ref FROM claims WHERE state='COMPLETED' ORDER BY key").fetchall()
            for (result_ref,) in rows:
                entry = _parse_entry(result_ref)
                refs.add(_blob(entry["speech"]).digest); refs.add(_blob(entry["receipt"]).digest)
            return frozenset(refs)
        finally:
            claims.close(); leases.close()

    def orphan_blobs(self):
        referenced = self.referenced_digests(); out=[]
        base = self.root / "cas" / "blobs" / "sha256"
        if not base.exists(): return ()
        for path in base.rglob("*"):
            if path.is_file():
                name = path.name
                if not HEX64.fullmatch(name):
                    raise AudioError("SEGMENT_CACHE_UNEXPECTED_CAS_MEMBER")
                if name not in referenced: out.append(path)
        return tuple(sorted(out))

    def prune_orphans(self, *, dry_run=True, max_delete=1000):
        if type(dry_run) is not bool: raise AudioError("SEGMENT_CACHE_PRUNE_MODE")
        integer(max_delete, "max delete", 1, 10000)
        orphans = self.orphan_blobs()
        if len(orphans) > max_delete:
            raise AudioError("SEGMENT_CACHE_PRUNE_BUDGET")
        rows = [{"digest": p.name, "bytes": p.stat().st_size} for p in orphans]
        if not dry_run:
            for p in orphans:
                st = p.lstat()
                if not stat.S_ISREG(st.st_mode) or st.st_nlink != 1:
                    raise AudioError("SEGMENT_CACHE_PRUNE_UNSAFE")
                p.unlink()
        return {"dry_run": dry_run, "orphans": rows, "deleted": 0 if dry_run else len(rows),
                "scope": "DEDICATED_SEGMENT_CACHE_ORPHANS_ONLY", "product_accepted": False}
