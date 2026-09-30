"""Fixed-roster native campaign requests. Hashes bind inputs; they are not approvals."""
from __future__ import annotations
from dataclasses import asdict, fields, dataclass
import hashlib
import json
from pathlib import Path

from ..models import BenchmarkError, canonical_json, strict_loads, digest, digest_string
from ..av.custody import Limits
from ..adoption.contracts import ExecutionContext
from ..native_qa import bridge

SCHEMA = 'bie.eval.native-campaign/1'
PIN = json.loads(Path(__file__).with_name('pin.json').read_text())
MAX_PLAN_BYTES = 2_000_000


def require(ok, code):
    if not ok:
        raise BenchmarkError(code)


def shape(obj, keys, code):
    require(type(obj) is dict and set(obj) == set(keys), code)
    return obj


def runtime_inventory():
    """Runtime bytes from this staged bie namespace, not a full repository tree."""
    root = Path(__file__).resolve().parents[3]
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts
            and p.suffix != '.pyc'}


def runtime_digest():
    return digest(runtime_inventory())


def verify_native_core():
    bridge.verify_native_runtime()
    from bie.qa.lifecycle_quality_v2 import durable
    root = Path(durable.__file__).resolve().parents[3]
    for row in PIN['files']:
        # Original canonical CLI bytes are recorded as preimage; explicit caller
        # adoption is a separately recorded local patch, not an unchanged pin.
        if row['path'].endswith('/__main__.py'):
            continue
        path = root / row['path']
        require(not path.is_symlink() and path.is_file(), 'CAMPAIGN_NATIVE_SOURCE_MISSING')
        raw = path.read_bytes()
        require(len(raw) == row['size_bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
                'CAMPAIGN_NATIVE_CODE_PIN_MISMATCH')


def content_effect(job, policy_sha256, limits):
    """Ignore labels/paths; repeated bytes + criteria are one logical attempt.

    Scope: aliases inside this fixed campaign. A separate campaign/database is
    not a globally coordinated benchmark attempt and cannot authorize release.
    """
    artifacts = sorted([a['role'], a['sha256'], a['size']]
                       for a in job['candidate_bundle']['candidate']['artifacts'])
    checks = []
    for row in sorted(job['checks'], key=lambda r: r['metric_id']):
        c = strict_loads(canonical_json(row['candidate']))
        for key in ('media', 'captions'):
            if c.get(key) is not None:
                c[key].pop('path', None)
        checks.append({'metric_id': row['metric_id'], 'reference': row['reference'], 'candidate': c})
    # Reference changes are new criteria, never a rerun of the same pinned job.
    return digest({'artifacts': artifacts, 'checks': checks, 'policy': policy_sha256, 'limits': limits})


@dataclass(frozen=True, init=False, slots=True)
class Plan:
    """Immutable serialized plan; nested inputs are copied at every public read."""
    _raw: str
    sha256: str
    effects: tuple

    def __init__(self, value, expected_sha256):
        raw = canonical_json(value)
        require(digest(value) == digest_string(expected_sha256), 'CAMPAIGN_PLAN_PIN_MISMATCH')
        data = strict_loads(raw)
        shape(data, ('schema_version', 'campaign_id', 'revision', 'runtime_sha256', 'policy_sha256',
                     'as_of', 'limits', 'lease_policy', 'jobs'), 'CAMPAIGN_PLAN_FIELDS')
        require(data['schema_version'] == SCHEMA, 'CAMPAIGN_SCHEMA')
        require(data['revision'] == PIN['commit'], 'CAMPAIGN_REVISION_PIN')
        from bie.qa.release_v2.contracts import token, integer, safe_relative_path
        from bie.qa.release_v2.codec import bundle_from_dict
        from bie.qa.release_v2.policy import enterprise_policy
        from bie.qa.lifecycle_quality_v2.durable import LeasePolicy
        token(data['campaign_id'], 'campaign'); integer(data['as_of'], 'as_of')
        require(data['policy_sha256'] == enterprise_policy().content_digest, 'CAMPAIGN_RELEASE_POLICY_PIN')
        digest_string(data['runtime_sha256'])
        shape(data['limits'], [f.name for f in fields(Limits)], 'CAMPAIGN_EXPLICIT_LIMITS')
        limits = Limits(**data['limits'])
        shape(data['lease_policy'], ('attempts', 'lease_seconds'), 'CAMPAIGN_LEASE_FIELDS')
        lease = LeasePolicy(**data['lease_policy'])
        require(lease.attempts == 1, 'CAMPAIGN_SINGLE_ATTEMPT_REQUIRED')
        require(lease.lease_seconds >= 3 * limits.deadline_s + 30, 'CAMPAIGN_LEASE_BUDGET')
        require(type(data['jobs']) is list and 1 <= len(data['jobs']) <= 128, 'CAMPAIGN_ROSTER_COUNT')
        ids, effects = set(), {}
        for job in data['jobs']:
            shape(job, ('job_id', 'artifact_subdir', 'candidate_bundle', 'expected_candidate_digest',
                        'checks', 'expected_checks_digest'), 'CAMPAIGN_JOB_FIELDS')
            token(job['job_id'], 'job'); safe_relative_path(job['artifact_subdir'])
            require(job['job_id'] not in ids, 'CAMPAIGN_DUPLICATE_JOB_ID'); ids.add(job['job_id'])
            bundle = bundle_from_dict(job['candidate_bundle'])
            require(not bundle.evidence, 'CAMPAIGN_INJECTED_EVIDENCE')
            require(bundle.candidate.revision == PIN['commit'], 'CAMPAIGN_CANDIDATE_REVISION')
            require(bundle.candidate.content_digest == digest_string(job['expected_candidate_digest']),
                    'CAMPAIGN_CANDIDATE_PIN')
            require(digest(job['checks']) == digest_string(job['expected_checks_digest']), 'CAMPAIGN_CHECKS_PIN')
            bridge._checks(job['checks'], bundle.candidate, ExecutionContext(Path('.'), limits))
            effect = content_effect(job, data['policy_sha256'], data['limits'])
            require(effect not in effects.values(), 'CAMPAIGN_CONTENT_ALIAS')
            effects[job['job_id']] = effect
        object.__setattr__(self, "_raw", raw)
        object.__setattr__(self, "sha256", expected_sha256)
        # Keep only immutable pairs; a caller cannot replace an effect in place.
        object.__setattr__(self, "effects", tuple(sorted(effects.items())))

    def data(self):
        return strict_loads(self._raw)

    def job(self, job_id):
        for row in self.data()['jobs']:
            if row['job_id'] == job_id:
                return row
        raise BenchmarkError('CAMPAIGN_UNKNOWN_JOB')

    def effect(self, job_id):
        self.job(job_id)
        return dict(self.effects)[job_id]
