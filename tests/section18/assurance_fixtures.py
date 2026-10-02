"""Authored gate candidate + projection-only repair fixtures, never live proof."""
from dataclasses import asdict
import hashlib
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.qa.release_v2.contracts import ArtifactRef,ReleaseCandidate,EvidenceBundle,digest,VERSION
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.repair_v2.models import Snapshot,RepairPolicy,FailureRule,OwnerRoute,CheckNode,RepairPlan,Failure

def gates(service,p,run,root):
    from apps.operator.artifacts import ProductArtifacts
    art=ProductArtifacts(service);folder=root/'authored-gate-candidate';folder.mkdir(exist_ok=True)
    with art.context(p,run,'publish') as (db,body,native):
        records=art.inventory(db,body,native);source='source-'+body['native_job_id'][4:]
        refs=[]
        for role,aid,raw in [('source',source,art.canonical_api(records,native).content(source)),
            ('video','fixture-video',b'Authored non-media QA diagnostic'),('game','fixture-game',b'Authored non-playable QA diagnostic')]:
            blob=native.cas.put_bytes(raw)
            if role!='source':native.persistence.register_artifact(PersistedArtifactRecord(aid,'fixture.'+role,'sha256',blob.digest,
                blob.size,body['native_job_id'],'QA',False,{'evidence_origin':'SYNTHETIC_TEST'},[source]))
            path=role+'.bin';(folder/path).write_bytes(raw)
            refs.append(ArtifactRef(aid,path,blob.digest,len(raw),role))
        candidate=ReleaseCandidate(VERSION,'authored-candidate',body['native_job_id'],'47cafba8975061555764c3c579ae6daad696ae64',tuple(refs))
    return ReleaseEvaluator(),EvidenceBundle(VERSION,candidate,()),folder

def repair_data(body,source_id,status='REJECTED'):
    """Only a unit projection specimen, NOT a Journal or native worker receipt."""
    source=ArtifactRef(source_id,'source/input.bin',body['source_hash'],100,'source')
    before=ArtifactRef('generated-before','generated/request.json',digest('before'),10,'support')
    snap=Snapshot(body['native_job_id'],'47cafba8975061555764c3c579ae6daad696ae64',(source,before))
    policy=RepairPolicy('operator-repair-policy',(FailureRule('BIE-QA-SOURCE-001','DEFECT','CONTENT','BI',True),),
        (OwnerRoute('BI',('generated/request.json',),('check-source',)),),(CheckNode('check-source',()),),('check-source',))
    failure=Failure('failure-one','BIE-QA-SOURCE-001','DEFECT','subject','BLOCKER','CONTENT','BI',True,digest('native-report'))
    plan=RepairPlan(digest('batch'),snap.content_digest,policy.content_digest,(failure,),('report-one',),False,('REPAIR_APPROVAL_REQUIRED',))
    if status=='STAGED_FOR_REVIEW':
        from dataclasses import replace
        plan=replace(plan,authenticated=True,diagnostics=())
    reserved=dict(kind='RESERVED',attempt=1,proposal_id='proposal-one',proposal_digest=digest('proposal'),effect_digest=digest('effect'),
        reserved_at=1000,reserved_bytes=20,reserved_seconds=10)
    binding=dict(run_id=snap.run_id,revision=snap.revision,snapshot_digest=snap.content_digest,policy_digest=policy.content_digest)
    export=dict(binding=binding,events=[reserved],chain_head=digest('UNIT_PROJECTION_ONLY'),product_accepted=False)
    if status=='PENDING':return export,plan,snap,policy,()
    candidate=Snapshot(snap.run_id,snap.revision,(source,ArtifactRef('generated-before','generated/request.json',digest('after'),20,'support')))
    outcomes=[dict(check_id='check-source',candidate_digest=candidate.content_digest,policy_digest=policy.content_digest,status='PASS',
        diagnostics=(),witness_digest=digest('authored-unit-check'))] if status=='STAGED_FOR_REVIEW' else []
    receipt=dict(schema_version='bie.qa.repair-attempt/1',attempt=1,proposal_id=reserved['proposal_id'],proposal_digest=reserved['proposal_digest'],
        base_digest=snap.content_digest,policy_digest=policy.content_digest,plan_digest=plan.content_digest,status=status,
        diagnostics=[] if outcomes else ['REPAIR_REVALIDATION_NOT_PASS'],candidate=asdict(candidate) if outcomes else None,
        candidate_digest=candidate.content_digest if outcomes else '',staged_directory='PRIVATE_PATH_MUST_NOT_ESCAPE',required_checks=['check-source'],
        invalidated_previous_checks=['check-source'],outcomes=outcomes,worker_error='',worker_elapsed_ms=1,worker_executed=bool(outcomes),
        original_files_written=False,canonical_repository_modified=False,product_accepted=False,downstream_previous_evidence_reusable=False,
        hostile_code_sandbox_verified=False,remaining_failure_ids=['failure-one'],promotion_requires='review')
    receipt['receipt_digest']=digest(receipt)
    export['events'].append(dict(kind='FINISHED',attempt=1,status=status,receipt_digest=receipt['receipt_digest']))
    receipt['journal_head']=export['chain_head'];return export,plan,snap,policy,(receipt,)

def publish_gates(service,p,run,root):
    from apps.operator.assurance import Assurance
    evaluator,bundle,folder=gates(service,p,run,root)
    return Assurance(service).bind_gates(p,run,evaluator,bundle,folder,as_of=1000,evidence_origin='SYNTHETIC_TEST')
