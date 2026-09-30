"""Bind the canonical BenchmarkAPI to a fixed, provenance-bound native campaign.

This is a synchronous library/operator API, not a network server or a production
queue. Trusted operators provision the campaign, artifact root and shared budget.
Untrusted request data cannot select those paths, a Python runner, or a policy.
"""
from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path

from ..models import canonical_json, strict_loads, digest, ident
from ..native_campaign.contracts import Plan, require, runtime_digest
from ..native_campaign.runtime import Campaign, private_directory, write_once
from .admission import Admission

SCHEMA = 'bie.eval.native-api/1'
PIN = json.loads(Path(__file__).with_name('pin.json').read_text())


def _checkout_blob_bytes(raw):
    """Recover the exact LF Git blob from an otherwise identical CRLF checkout."""
    if b'\r\n' in raw and b'\r' not in raw.replace(b'\r\n', b''):
        return raw.replace(b'\r\n', b'\n')
    return raw


def verify_native_api():
    module = importlib.import_module('bie.infrastructure.benchmark_api')
    path = Path(module.__file__)
    require(path.is_file() and not path.is_symlink(), 'API_CANONICAL_FILE')
    raw = path.read_bytes()
    # Git may materialize the pinned LF blob with CRLF in a Windows checkout.
    # Accept only that byte-for-byte line-ending conversion, never edited code.
    canonical = _checkout_blob_bytes(raw)
    require(len(canonical) == PIN['size_bytes'] and hashlib.sha256(canonical).hexdigest() == PIN['sha256'],
            'API_CANONICAL_PIN')
    require(hashlib.sha1(b'blob '+str(len(canonical)).encode()+b'\0'+canonical).hexdigest() == PIN['git_blob_sha'],
            'API_CANONICAL_GIT_BLOB')
    return module.BenchmarkAPI


class PlanRegistry:
    def __init__(self, plan):
        require(type(plan) is Plan, 'API_PLAN_TYPE')
        self.plan = plan

    def cases(self):
        return tuple(dict(case_id=j['job_id'], domain='AV_TECHNICAL',
                          plan_sha256=self.plan.sha256,
                          candidate_sha256=j['expected_candidate_digest'],
                          expected_artifact_refs=j['candidate_bundle']['candidate']['artifacts'],
                          metric_ids=[r['metric_id'] for r in j['checks']],
                          required=True, benchmark_scope='DEVELOPMENT_THREE_AV_METRICS')
                     for j in self.plan.data()['jobs'])

    def get(self, case_id):
        ident(case_id)
        return next((row for row in self.cases() if row['case_id'] == case_id), None)


def validate_refs(job, supplied):
    require(type(supplied) in (tuple,list) and 1 <= len(supplied) <= 4096, 'API_ARTIFACT_REFS_TYPE_OR_COUNT')
    rows = strict_loads(canonical_json(list(supplied)))
    keys = {'artifact_id','path','sha256','size','role'}
    require(all(type(row) is dict and set(row) == keys for row in rows), 'API_ARTIFACT_REF_FIELDS')
    require(all(type(row['artifact_id']) is str for row in rows), 'API_ARTIFACT_REF_ID')
    require(len({r['artifact_id'] for r in rows}) == len(rows), 'API_DUPLICATE_ARTIFACT_REF')
    expected = job['candidate_bundle']['candidate']['artifacts']
    sort = lambda values: sorted(values,key=lambda row:row['artifact_id'])
    # canonical bytes distinguish e.g. bool True from integer 1.
    require(canonical_json(sort(rows)) == canonical_json(sort(expected)), 'API_ARTIFACT_REFS_MISMATCH')
    return rows


class CampaignRunner:
    def __init__(self, campaign, artifact_root, admission, owner):
        require(type(campaign) is Campaign and type(admission) is Admission, 'API_RUNTIME_TYPES')
        self.campaign, self.artifact_root, self.admission = campaign, private_directory(artifact_root), admission
        self.owner = ident(owner)
        self._ready()

    def _ready(self):
        verify_native_api()
        self.campaign._ready()
        configuration = self.admission.configuration
        require(configuration['runtime_sha256'] == runtime_digest() == self.campaign.data['runtime_sha256'] and
                configuration['policy_sha256'] == self.campaign.data['policy_sha256'], 'API_REGISTRY_SCOPE_MISMATCH')
        # A missing/tampered registry must be detected even for read/replay calls.
        self.admission.snapshot()

    def _native_finished(self, case_id):
        summary = self.campaign.summary()
        row = next(r for r in summary['jobs'] if r['job_id'] == case_id)
        require(row['state'] == 'FINISHED' and row['result_sha256'] is not None, 'API_NATIVE_RESULT_NOT_FINISHED')
        result = self.campaign._read_result(self.campaign.plan.job(case_id), row['result_sha256'])
        evaluation = result.get('evaluation')
        if evaluation is not None:
            require(evaluation.get('release_authorized') is False and evaluation.get('product_accepted') is False,
                    'API_NATIVE_PROMOTION')
            if evaluation.get('native_component_consumer_executed') is True:
                qa = evaluation.get('native_qa_report',{})
                require(qa.get('release_status') == 'BLOCKED' and len(qa.get('gate_results',[])) == 28,
                        'API_NATIVE_GATE_COVERAGE')
        return row['result_sha256'], result

    def _reply(self, case_id, sha, result, replayed):
        return dict(schema_version=SCHEMA, case_id=case_id, plan_sha256=self.campaign.plan.sha256,
                    canonical_api_commit=PIN['commit'], canonical_api_git_blob=PIN['git_blob_sha'],
                    canonical_api_executed=False, replayed=replayed, result_sha256=sha, result=result,
                    admission_scope=self.admission.configuration['scope_id'],
                    cross_campaign_guard='SAME_OPERATOR_REGISTRY_ONLY',
                    status='BLOCKED', release_authorized=False, product_accepted=False)

    def run(self, case_id, artifact_refs):
        self._ready()
        job = self.campaign.plan.job(case_id)
        validate_refs(job, artifact_refs)
        effect = self.campaign.plan.effect(case_id)
        registered = next((r for r in self.admission.snapshot()['attempts'] if r['effect'] == effect),None)
        state = next(r for r in self.campaign.summary()['jobs'] if r['job_id'] == case_id)
        require(registered is not None or state['state'] == 'NOT_RUN', 'API_UNGOVERNED_NATIVE_ATTEMPT')
        admission = self.admission.reserve(effect, self.campaign.plan.sha256, case_id)
        if admission['replayed']:
            sha, result = self._native_finished(case_id)
            require(sha == admission['result_sha256'], 'API_REPLAY_RECEIPT_MISMATCH')
            return self._reply(case_id,sha,result,True)
        # A crash after reservation leaves it RESERVED. It cannot admit a second
        # collector. Explicit reconcile reads native evidence without executing.
        try:
            native = self.campaign.run_job(case_id,self.artifact_root,self.owner)
            require(native.get('replayed') is False, 'API_UNGOVERNED_REPLAY')
            sha, result = self._native_finished(case_id)
        except Exception as exc:
            receipt = dict(plan=self.campaign.plan.sha256, case_id=case_id,
                           error_code=getattr(exc,'code','API_DISPATCH_EXCEPTION'),
                           exception_type=type(exc).__name__, status='BLOCKED')
            raw = canonical_json(receipt).encode('utf-8')
            sha = hashlib.sha256(raw).hexdigest()
            target = self.campaign.audit / ('api-'+sha+'.json')
            private_directory(self.campaign.audit)
            write_once(target,raw)
            self.admission.block(effect,self.campaign.plan.sha256,case_id,sha,'DISPATCH_FAILED')
            raise
        self.admission.finish(effect,self.campaign.plan.sha256,case_id,sha)
        return self._reply(case_id,sha,result,False)

    def reconcile(self, case_id):
        """Resolve native-finished/registry-reserved crash window; NEVER re-execute."""
        self._ready(); job = self.campaign.plan.job(case_id)
        effect = self.campaign.plan.effect(case_id)
        row = next((r for r in self.admission.snapshot()['attempts'] if r['effect'] == effect),None)
        require(row is not None and row['plan'] == self.campaign.plan.sha256 and row['job'] == case_id,
                'API_ADMISSION_BINDING')
        require(row['state'] in ('RESERVED','FINISHED'), 'API_ADMISSION_TERMINAL')
        sha, result = self._native_finished(case_id)
        self.admission.finish(effect,self.campaign.plan.sha256,case_id,sha)
        reply = self._reply(case_id,sha,result,True)
        reply.update(canonical_api_executed=False, reconciled_without_execution=True)
        return reply


class Service:
    """Bounded request facade that actually delegates to canonical BenchmarkAPI."""
    def __init__(self, campaign, artifact_root, admission, owner='local-api-operator'):
        self.registry = PlanRegistry(campaign.plan)
        self.runner = CampaignRunner(campaign,artifact_root,admission,owner)
        native = verify_native_api()
        self.native = native(self.registry,self.runner)

    def cases(self, domain=None):
        self.runner._ready()
        if domain is not None:
            ident(domain)
        return self.native.cases(domain)

    def run(self, case_id, artifact_refs):
        ident(case_id)
        require(type(artifact_refs) in (tuple,list) and 1 <= len(artifact_refs) <= 4096,
                'API_ARTIFACT_REFS_TYPE_OR_COUNT')
        # Strict bounded JSON before the original API materializes tuple(refs).
        detached = strict_loads(canonical_json(list(artifact_refs)))
        self.runner._ready()
        result = self.native.run(case_id,detached)
        return dict(result,canonical_api_executed=True)

    def summary(self):
        self.runner._ready()
        result = self.runner.campaign.summary()
        attempts = {r['effect']:r for r in self.runner.admission.snapshot()['attempts']}
        for row in result['jobs']:
            claim = attempts.get(self.runner.campaign.plan.effect(row['job_id']))
            row['api_admission_state'] = 'NOT_ADMITTED' if claim is None else claim['state']
            row['api_admission_campaign_matches'] = (claim is not None and claim['plan'] == self.runner.campaign.plan.sha256)
        result['api_admission_scope'] = self.runner.admission.configuration['scope_id']
        result['cross_campaign_guard'] = 'SAME_OPERATOR_REGISTRY_ONLY'
        return result
