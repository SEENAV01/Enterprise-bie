"""H3-002: exact media, requests and signed evidence in existing BIE CAS/SQLite.

The canonical implementations are injected/imported, not recreated. No separate
hash/lineage scheme or private key store is introduced. Root is service-owned.
"""
from __future__ import annotations
from contextlib import contextmanager
from dataclasses import asdict
from pathlib import Path
import hashlib
import os
import stat
from bie.infrastructure.artifact_store import FileSystemCAS, BlobRef
from bie.director.director_durable_recovery import SQLiteArtifactCatalog
from bie.director.director_artifacts import DirectorArtifactIO, reference
from bie.bie_core.artifact_contracts import ArtifactEnvelope, ProducerIdentity, ProvenanceSource, ProvenanceSummary
from .common import AudioError, fingerprint, strict_json
from .acoustic_contract import canonical, plain, fields, validate_job
from .acoustic_evidence import verify_receipt
from .acoustic_assessment import assess_receipt
from .acoustic_repair import plan_repairs
from .tts_cache import key_lock
from .durable_contract import DurablePolicy, SCOPE, validate_request

PRODUCER = ProducerIdentity('bie.audio.durable', '1.0.0', 'deterministic')
METADATA = {'requires_review':True, 'product_accepted':False, 'scope':SCOPE}


def private_root(path):
    p = Path(path).absolute()
    if any(x.is_symlink() for x in (p, *p.parents)):
        raise AudioError('DURABLE_ROOT_SYMLINK')
    p.mkdir(parents=True, exist_ok=True, mode=0o700)
    st = p.stat()
    if not p.is_dir() or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise AudioError('DURABLE_ROOT_NOT_PRIVATE')
    return p


def check_tree(root, policy):
    count = total = 0
    for folder, dirs, files in os.walk(root, followlinks=False):
        for name in (*dirs, *files):
            p = Path(folder)/name
            s = p.lstat()
            if s.st_uid != os.getuid() or s.st_mode & 0o022 or not (stat.S_ISREG(s.st_mode) or stat.S_ISDIR(s.st_mode)):
                raise AudioError('DURABLE_UNSAFE_STORAGE_MEMBER')
            count += 1
            if stat.S_ISREG(s.st_mode):
                total += s.st_size
                if s.st_nlink != 1 or s.st_size > policy.max_artifact_bytes:
                    raise AudioError('DURABLE_ARTIFACT_BUDGET_OR_HARDLINK')
            if count > policy.max_files or total > policy.max_store_bytes:
                raise AudioError('DURABLE_STORE_BUDGET')
    return count, total


class AudioArtifactStore:
    """Each short operation reopens the durable index under a cooperating lock.

    This avoids stale in-memory catalog views across AUDIO processes. Other BIE
    writers of this dedicated AUDIO root must use the same locking protocol.
    """
    def __init__(self, root, *, policy=DurablePolicy()):
        if type(policy) is not DurablePolicy:
            raise AudioError('DURABLE_POLICY_TYPE')
        self.root, self.policy = private_root(root), policy

    @contextmanager
    def session(self):
        private_root(self.root)
        with key_lock(self.root/'catalog.lock', timeout=self.policy.lock_timeout_seconds):
            check_tree(self.root, self.policy)
            cas = FileSystemCAS(self.root/'cas')
            catalog = SQLiteArtifactCatalog(cas, self.root/'artifacts.sqlite')
            try:
                if catalog.verify_durable_index():
                    raise AudioError('DURABLE_INDEX_CORRUPT')
                yield DirectorArtifactIO(catalog)
                if catalog.verify_durable_index():
                    raise AudioError('DURABLE_INDEX_CORRUPT')
                check_tree(self.root, self.policy)
            finally:
                catalog.close()

    def _budget(self, *values):
        for value in values:
            if len(value) > self.policy.max_artifact_bytes:
                raise AudioError('DURABLE_ARTIFACT_BUDGET')

    def put(self, request, wav, receipt, trust, *, now=None):
        request, receipt, trust = plain(request), plain(receipt), plain(trust)
        policy = validate_request(request, wav)
        if policy != self.policy:
            raise AudioError('DURABLE_POLICY_MISMATCH')
        job = request['job']
        measurement = verify_receipt(receipt, job, trust, now=now)
        if receipt['payload']['key_id'] != request['key_id'] or measurement['runtime_fingerprint'] != request['runtime_fingerprint']:
            raise AudioError('DURABLE_EVALUATOR_BINDING')
        assessment = assess_receipt(receipt, job, trust, now=now)
        repairs = plan_repairs(job, receipt, trust, now=now)
        self._budget(wav, canonical(request), canonical(receipt))
        with self.session() as io:
            count, total = check_tree(self.root, self.policy)
            # Conservative reservation; no silent quota overshoot before writing.
            if count + 12 > policy.max_files or total + len(wav) + 4*len(canonical(request)) + 4*len(canonical(receipt)) + 100_000 > policy.max_store_bytes:
                raise AudioError('DURABLE_STORE_BUDGET')
            blob = io.catalog.cas.put_bytes(wav)
            refs = sorted({r for s in job['segments'] for span in s['source_spans'] for r in span['source_refs']})
            provenance = ProvenanceSummary([ProvenanceSource(r,
                {'kind':'declared-audio-source-reference','acoustic_job':job['fingerprint']}) for r in refs])
            # Not a fabricated PDF/Director artifact: this is an imported, mapped
            # delivered-media asset with explicitly declared source references.
            media = ArtifactEnvelope.create('source.asset','1.0.0',request['run_id'],PRODUCER,[],provenance,
                dict(METADATA), {'kind':'audio-mix-import','source_authority':'DECLARED_SOURCE_REFS_NOT_DIR_ACCEPTANCE',
                                 'blob':asdict(blob),'job':job})
            media_ref = io.put(media,'AUDIO:MEDIA:IMPORT')
            req_ref = io.derive('audio.acoustic.request',request['run_id'],[media_ref],request,
                stage_id='AUDIO:ACOUSTIC:REQUEST',metadata=dict(METADATA),producer=PRODUCER)
            payload = {'request':request, 'receipt':receipt, 'assessment_at_issue':assessment,
                       'repair_at_issue':repairs, 'issued_trust_fingerprint':fingerprint(trust),
                       'historical_issue_verification_only':True}
            self._budget(canonical(payload))
            result_ref = io.derive('audio.acoustic.evaluation',request['run_id'],[req_ref],payload,
                stage_id='AUDIO:ACOUSTIC:EVIDENCE',metadata=dict(METADATA),producer=PRODUCER,evidence=True)
            return asdict(result_ref)

    def load(self, ref, request, trust, *, now=None):
        request, trust = plain(request), plain(trust)
        if validate_request(request) != self.policy:
            raise AudioError('DURABLE_POLICY_MISMATCH')
        ref = reference(plain(ref))
        with self.session() as io:
            result = io.load(ref)
            if result.artifact_type != 'audio.acoustic.evaluation' or result.run_id != request['run_id'] or result.metadata != METADATA or len(result.parent_refs) != 1:
                raise AudioError('DURABLE_RESULT_KIND_OR_RUN')
            p = result.payload
            fields(p, ('request','receipt','assessment_at_issue','repair_at_issue','issued_trust_fingerprint','historical_issue_verification_only'))
            if p['request'] != request or p['historical_issue_verification_only'] is not True:
                raise AudioError('DURABLE_RESULT_STALE_REQUEST')
            req = io.load(result.parent_refs[0])
            if req.artifact_type != 'audio.acoustic.request' or req.payload != request or req.run_id != request['run_id'] or len(req.parent_refs) != 1:
                raise AudioError('DURABLE_REQUEST_PARENT_MISMATCH')
            media = io.load(req.parent_refs[0])
            if media.artifact_type != 'source.asset' or media.run_id != request['run_id'] or media.parent_refs or media.payload.get('job') != request['job']:
                raise AudioError('DURABLE_MEDIA_PARENT_MISMATCH')
            fields(media.payload, ('kind','source_authority','blob','job'))
            if media.payload['kind'] != 'audio-mix-import' or media.payload['source_authority'] != 'DECLARED_SOURCE_REFS_NOT_DIR_ACCEPTANCE':
                raise AudioError('DURABLE_SOURCE_AUTHORITY_CHANGED')
            blob = BlobRef(**media.payload['blob'])
            if type(blob.size) is not int or not 1 <= blob.size <= self.policy.max_artifact_bytes:
                raise AudioError('DURABLE_MEDIA_SIZE')
            wav = io.catalog.cas.get_bytes(blob)
            validate_request(request, wav)
            expected_sources = sorted({r for s in request['job']['segments'] for sp in s['source_spans'] for r in sp['source_refs']})
            expected_provenance = ProvenanceSummary([ProvenanceSource(r,
                {'kind':'declared-audio-source-reference','acoustic_job':request['job']['fingerprint']}) for r in expected_sources])
            if any(x.provenance_summary != expected_provenance for x in (media,req,result)):
                raise AudioError('DURABLE_PROVENANCE_CHANGED')
        measured = verify_receipt(p['receipt'],request['job'],trust,now=now)
        if measured['runtime_fingerprint'] != request['runtime_fingerprint'] or p['receipt']['payload']['key_id'] != request['key_id']:
            raise AudioError('DURABLE_EVALUATOR_BINDING')
        assessment = assess_receipt(p['receipt'],request['job'],trust,now=now)
        repairs = plan_repairs(request['job'],p['receipt'],trust,now=now)
        # A later trust revision is allowed only after fresh authentication;
        # historical assessment is never returned as current authorization.
        return {'artifact_ref':plain(asdict(ref)), 'receipt':plain(p['receipt']),
                'assessment':assessment, 'repair_plan':repairs,
                'media_sha256':hashlib.sha256(wav).hexdigest(),
                'request_fingerprint':request['fingerprint'], 'current_trust_fingerprint':fingerprint(trust),
                'scope':SCOPE,'product_accepted':False,'signature_reverified':True}

    def inspect(self):
        with self.session() as io:
            media_verified = 0
            for record in io.catalog.records.values():
                envelope = io.load(record.artifact_id)
                if envelope.artifact_type == 'source.asset':
                    fields(envelope.payload, ('kind','source_authority','blob','job'))
                    blob = BlobRef(**envelope.payload['blob'])
                    if type(blob.size) is not int or not 1 <= blob.size <= self.policy.max_artifact_bytes:
                        raise AudioError('DURABLE_MEDIA_SIZE')
                    wav = io.catalog.cas.get_bytes(blob)
                    validate_job(envelope.payload['job'],wav)
                    media_verified += 1
            return {'artifacts':len(io.catalog.records), 'evidence_artifacts':sum(r.evidence for r in io.catalog.records.values()),
                    'media_blobs_verified':media_verified,
                    'index_problems':list(io.catalog.verify_durable_index()),
                    'scope':'Storage integrity, not current issuer authentication or acoustic acceptance',
                    'product_accepted':False}
