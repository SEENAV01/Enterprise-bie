"""Run a fixed campaign through the REAL Section16 lease journal and QA evaluator.

Use an operator-owned private filesystem. This is local fencing, not distributed
worker isolation, attestation, global benchmark attempt accounting or publication.
A FINISHED journal job means collection completed, NOT that QA passed.
"""
from __future__ import annotations
from dataclasses import asdict
import hashlib
import os
from pathlib import Path
import stat
import time

from ..models import BenchmarkError, canonical_json, strict_loads, digest
from ..native_qa.__main__ import read_bounded
from ..native_qa import bridge
from ..av.custody import Limits
from ..adoption.contracts import ExecutionContext
from .contracts import Plan, SCHEMA, require, runtime_digest, verify_native_core


def private_directory(path):
    path = Path(path).absolute()
    for p in (path,) + tuple(path.parents):
        require(not p.is_symlink(), 'CAMPAIGN_DIRECTORY_SYMLINK')
    require(path.is_dir(), 'CAMPAIGN_DIRECTORY_REQUIRED')
    return path


def write_once(path, raw):
    """Exclusive durable write; an interrupted file is never silently repaired."""
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    if os.name == 'posix':
        parent = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try: os.fsync(parent)
        finally: os.close(parent)


class Campaign:
    def __init__(self, root, plan, *, _initializing=False):
        require(type(plan) is Plan, 'CAMPAIGN_PLAN_TYPE')
        self.root = private_directory(root)
        self.plan = plan
        # Validate exact on-disk plan before importing/claiming native state.
        raw = read_bounded(self.root / 'PLAN.json', 2_000_000)
        require(digest(strict_loads(raw)) == plan.sha256, 'CAMPAIGN_STORED_PLAN_CHANGED')
        require(runtime_digest() == self.data['runtime_sha256'], 'CAMPAIGN_RUNTIME_CHANGED')
        verify_native_core()
        self.results = private_directory(self.root / 'results')
        self.audit = private_directory(self.root / 'audit')
        self._database_paths()
        require(_initializing or (self.root / 'campaign.sqlite').is_file(), 'CAMPAIGN_DATABASE_MISSING')
        from bie.qa.lifecycle_quality_v2.common import Binding
        from bie.qa.lifecycle_quality_v2.durable import LeasePolicy, LeaseJournal
        self.policy = LeasePolicy(**self.data['lease_policy'])
        binding = Binding(self.data['campaign_id'], self.data['revision'], plan.sha256, self.policy.content_digest)
        self.journal = LeaseJournal(self.root / 'campaign.sqlite', binding, self.policy)

    @property
    def data(self):
        return self.plan.data()

    @classmethod
    def create(cls, root, plan):
        root = Path(root).absolute()
        private_directory(root.parent)
        require(type(plan) is Plan, 'CAMPAIGN_PLAN_TYPE')
        require(runtime_digest() == plan.data()['runtime_sha256'], 'CAMPAIGN_RUNTIME_CHANGED')
        root.mkdir(mode=0o700, exist_ok=False)
        (root / 'results').mkdir(mode=0o700)
        (root / 'audit').mkdir(mode=0o700)
        write_once(root / 'PLAN.json', (canonical_json(plan.data()) + '\n').encode())
        return cls(root, plan, _initializing=True)

    def _database_paths(self):
        private_directory(self.root)
        for name in ('campaign.sqlite', 'campaign.sqlite-wal', 'campaign.sqlite-shm', 'campaign.sqlite-journal'):
            p = self.root / name
            require(not p.is_symlink(), 'CAMPAIGN_DATABASE_SYMLINK')
            if p.exists():
                s = p.stat()
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, 'CAMPAIGN_DATABASE_FILE')

    def _ready(self):
        self._database_paths()
        require((self.root / 'campaign.sqlite').is_file(), 'CAMPAIGN_DATABASE_MISSING')
        require(digest(strict_loads(read_bounded(self.root / 'PLAN.json', 2_000_000))) == self.plan.sha256,
                'CAMPAIGN_STORED_PLAN_CHANGED')
        require(runtime_digest() == self.data['runtime_sha256'], 'CAMPAIGN_RUNTIME_CHANGED')
        private_directory(self.results); private_directory(self.audit)

    def _store_result(self, result):
        raw = (canonical_json(result) + '\n').encode()
        result_sha = hashlib.sha256(raw).hexdigest()
        path = self.results / (result_sha + '.json')
        # No overwrite. A matching orphan from a previous interrupted attempt
        # is readable evidence, not automatic authority to finish that attempt.
        try: write_once(path, raw)
        except FileExistsError:
            require(read_bounded(path, 2_000_000) == raw, 'CAMPAIGN_RESULT_COLLISION')
        return result_sha

    def _read_result(self, job, result_sha):
        from ..models import digest_string
        digest_string(result_sha)
        raw = read_bounded(self.results / (result_sha + '.json'), 2_000_000)
        require(hashlib.sha256(raw).hexdigest() == result_sha, 'CAMPAIGN_RESULT_HASH')
        result = strict_loads(raw)
        require(result.get('schema_version') == SCHEMA and result.get('plan_sha256') == self.plan.sha256
                and result.get('job_id') == job['job_id']
                and result.get('effect_sha256') == self.plan.effect(job['job_id'])
                and result.get('candidate_sha256') == job['expected_candidate_digest']
                and result.get('runtime_sha256') == self.data['runtime_sha256'], 'CAMPAIGN_RESULT_BINDING')
        require(result.get('status') == 'BLOCKED' and result.get('release_authorized') is False
                and result.get('product_accepted') is False, 'CAMPAIGN_RESULT_PROMOTION')
        return result

    def run_job(self, job_id, artifact_root, owner):
        self._ready()
        job = self.plan.job(job_id)
        effect = self.plan.effect(job_id)
        claim = self.journal.claim(job_id, effect, owner, int(time.time()))
        if claim['replayed']:
            return dict(replayed=True, result=self._read_result(job, claim['result_digest']))
        result = dict(schema_version=SCHEMA, plan_sha256=self.plan.sha256, job_id=job_id,
                      effect_sha256=effect, candidate_sha256=job['expected_candidate_digest'],
                      runtime_sha256=self.data['runtime_sha256'], native_fencing_token=claim['token'],
                      status='BLOCKED', release_authorized=False, product_accepted=False)
        try:
            base = private_directory(artifact_root)
            source = private_directory(base / job['artifact_subdir'])
            require(source.is_relative_to(base), 'CAMPAIGN_ARTIFACT_ROOT_ESCAPE')
            from bie.qa.release_v2.codec import bundle_from_dict
            bundle = bundle_from_dict(job['candidate_bundle'])
            measured = bridge.execute(bundle.candidate, job['checks'],
                execution_context=ExecutionContext(source, Limits(**self.data['limits'])),
                as_of=self.data['as_of'], expected_candidate_digest=job['expected_candidate_digest'],
                expected_policy_digest=self.data['policy_sha256'], expected_checks_digest=job['expected_checks_digest'])
            # Partial AV/native-QA slice cannot promote release even if a future
            # upstream return shape changes. Fail closed until explicitly migrated.
            require(measured.get('release_authorized') is False and measured.get('product_accepted') is False
                    and measured.get('native_qa_report', {}).get('release_status') == 'BLOCKED',
                    'CAMPAIGN_UPSTREAM_PROMOTION')
            result['evaluation'] = measured
        except Exception as exc:
            result.update(error_code=getattr(exc, 'code', 'CAMPAIGN_EXECUTION_EXCEPTION'),
                          exception_type=type(exc).__name__, native_component_consumer_executed=False)
        self._ready()
        result_sha = self._store_result(result)
        # Native finish rejects expired/cancelled/replaced fencing tokens.
        # A crash or rejected finish leaves evidence on disk, never a PASS/retry.
        self.journal.finish(job_id, claim['token'], owner, int(time.time()), result_sha,
                            ('section17-campaign-summary',))
        return dict(replayed=False, result=self._read_result(job, result_sha))

    def run(self, artifact_root, owner):
        events = []
        for job in self.data['jobs']:
            try:
                row = self.run_job(job['job_id'], artifact_root, owner)
                events.append(dict(job_id=job['job_id'], replayed=row['replayed'], state='FINISHED'))
            except Exception as exc:
                events.append(dict(job_id=job['job_id'], state='BLOCKED',
                    error_code=getattr(exc, 'code', 'CAMPAIGN_DISPATCH_EXCEPTION'), exception_type=type(exc).__name__))
        return {'dispatch': events, 'summary': self.summary()}

    def summary(self):
        self._ready()
        exported = self.journal.export()
        states = {r['job_id']: r for r in exported['jobs']}
        planned = {r['job_id'] for r in self.data['jobs']}
        require(set(states) <= planned, 'CAMPAIGN_UNREGISTERED_JOB')
        rows = []
        for job in self.data['jobs']:
            state = states.get(job['job_id'])
            row = dict(job_id=job['job_id'], state='NOT_RUN' if state is None else state['state'],
                       release_status='BLOCKED', result_sha256=None, measurement_outcomes={})
            if state:
                require(state['effect_digest'] == self.plan.effect(job['job_id']), 'CAMPAIGN_JOB_EFFECT_CHANGED')
            if state and state['state'] == 'FINISHED':
                result = self._read_result(job, state['result_digest'])
                row.update(result_sha256=state['result_digest'],
                           measurement_outcomes=result.get('evaluation', {}).get('measurement_outcomes', {}),
                           error_code=result.get('error_code'))
            rows.append(row)
        finished = sum(row['state'] == 'FINISHED' for row in rows)
        return dict(schema_version=SCHEMA, plan_sha256=self.plan.sha256, status='BLOCKED',
            required_jobs=len(rows), finished_jobs=finished, uncompleted_jobs=len(rows)-finished, jobs=rows,
            native_journal_chain_head=exported['chain_head'], native_journal_event_count=exported['event_count'],
            outbox_count=len(self.journal.pending()), completion_is_not_acceptance=True,
            global_attempt_registry_verified=False, full_native_book_pipeline_executed=False,
            release_authorized=False, product_accepted=False)

    def cancel(self, job_id):
        """Fence an active attempt. Does not kill its process or retry its work."""
        self._ready(); self.plan.job(job_id)
        self.journal.cancel(job_id, int(time.time()))
        return self.summary()
