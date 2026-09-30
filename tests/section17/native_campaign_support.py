"""Authored AV interoperation fixtures; no autonomous book pipeline or learner study."""
from copy import deepcopy
from dataclasses import asdict, replace
from pathlib import Path
import hashlib
from native_qa_support import inputs, NOW, LIMITS
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.native_campaign.contracts import Plan, SCHEMA, PIN, runtime_digest
from bie.qa.release_v2.contracts import EvidenceBundle
from bie.qa.release_v2.policy import enterprise_policy


def request(root, kinds=('good',)):
    root = Path(root);root.mkdir(parents=True, exist_ok=True)
    jobs=[]
    for index,kind in enumerate(kinds):
        name=f'job-{index}-{kind}'; directory=root/name
        candidate,checks=inputs(directory)
        candidate=replace(candidate,candidate_id=name,run_id=name)
        if kind=='wrong-frame':
            checks[1]['reference']['frame_reference']['frame_chain_sha256']='a'*64
            checks[1]['expected_reference_sha256']=digest(checks[1]['reference'])
        elif kind=='corrupt':
            path=directory/'lesson.mkv';path.write_bytes(b'authored invalid media payload')
            sha=hashlib.sha256(path.read_bytes()).hexdigest()
            candidate=replace(candidate,artifacts=tuple(replace(a,sha256=sha,size=path.stat().st_size)
                    if a.role=='video' else a for a in candidate.artifacts))
            for row in checks:
                row['candidate']['media'].update(sha256=sha,size_bytes=path.stat().st_size)
                row['expected_candidate_sha256']=digest(row['candidate'])
        jobs.append(dict(job_id=name,artifact_subdir=name,candidate_bundle=EvidenceBundle('2.0.0',candidate,()).to_dict(),
            expected_candidate_digest=candidate.content_digest,checks=checks,expected_checks_digest=digest(checks)))
    return dict(schema_version=SCHEMA,campaign_id='authored-native-campaign',revision=PIN['commit'],
        runtime_sha256=runtime_digest(),policy_sha256=enterprise_policy().content_digest,as_of=NOW,
        limits=asdict(LIMITS),lease_policy={'attempts':1,'lease_seconds':180},jobs=jobs)


def plan(root,kinds=('good',)):
    value=request(root,kinds);return Plan(value,digest(value))
