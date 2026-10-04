"""Read-only native QA gate / repair history ports; never a replacement engine.

Gate evaluation is actually delegated. Repair attempts require the canonical
POSIX Journal to export its verified chain. No JSON publisher exists over HTTP.
Historical decisions are not current deployment authority or product acceptance.
"""
from dataclasses import asdict
from bie.qa.release_v2.evaluator import ReleaseEvaluator,EvaluationReport,GateResult,EvidenceCheck
from bie.qa.release_v2.contracts import EvidenceBundle,ContractError,digest as native_digest
from bie.qa.release_v2.policy import enterprise_policy
from bie.qa.repair_v2.journal import Journal
from bie.qa.repair_v2.models import RepairPlan,Snapshot,RepairPolicy,CheckOutcome
from .quality import Quality,label,hash_value,count,codes,safe_tree,MAX_RECORD,MAX_HISTORY
from .artifacts import pagination
from .contracts import require,strict_json,OperatorError
from .view_contracts import shape

KINDS=('gates','repairs')
GATE_STATUSES=('PASS','FAIL','ERROR','PENDING')

def gate_projection(report,bundle,policy):
    require(type(report) is EvaluationReport and type(bundle) is EvidenceBundle,'native_gate_report_required',400)
    require((report.bundle_digest,report.candidate_digest,report.policy_digest)==
        (bundle.content_digest,bundle.candidate.content_digest,policy.content_digest),'gate_receipt_binding',400)
    require(report.release_authorized is False and report.product_accepted is False,'gate_unauthorized_promotion',400)
    expected={g.gate_id:g for g in policy.gates}
    require(type(report.gate_results) is tuple and len(report.gate_results)==len(expected)<=128,
        'gate_inventory_invalid',400)
    rows=[];seen=set()
    for g in report.gate_results:
        require(type(g) is GateResult and g.gate_id in expected and g.gate_id not in seen,'gate_inventory_invalid',400)
        seen.add(g.gate_id);rule=expected[g.gate_id]
        require(g.owner==rule.owner and g.status in GATE_STATUSES,'gate_status_invalid',400)
        require(type(g.evidence) is tuple and len(g.evidence)<=128,'gate_evidence_limit',413)
        evidence=[]
        for e in g.evidence:
            require(type(e) is EvidenceCheck and e.status in ('PASS','FAIL','ERROR'),'gate_evidence_invalid',400)
            evidence.append(dict(evidence_id=label(e.evidence_id),evaluator_id=label(e.evaluator_id),status=e.status,
                reasons=codes(e.diagnostics),assurance=label(e.assurance),report_sha256=hash_value(e.report_sha256),
                trust_expires_at=count(e.trust_expires_at,2**53-1)))
        require(g.status!='PASS' or (evidence and all(e['status']=='PASS' for e in evidence)),
            'gate_status_invalid',400)
        rows.append(dict(gate_id=g.gate_id,owner=label(g.owner),status=g.status,reasons=codes(g.diagnostics),
            required_roles=list(rule.required_roles),minimum_independent_evaluators=rule.min_distinct_evaluators,
            evidence=evidence))
    blocked=sorted(g['gate_id'] for g in rows if g['status']!='PASS')
    require(sorted(report.blocking_gates)==blocked,'gate_blockers_invalid',400)
    reasons=codes(report.global_diagnostics)
    require(report.release_status in ('BLOCKED','CONTRACT_ONLY','READY_FOR_REVIEW') and
        ((not blocked and not reasons) or report.release_status in ('BLOCKED','CONTRACT_ONLY')),
        'gate_status_invalid',400)
    require(type(report.ready_for_review) is bool and report.ready_for_review==(report.release_status=='READY_FOR_REVIEW'),
        'gate_status_invalid',400)
    result=dict(attempt_id='gate-'+hash_value(native_digest(report.to_dict())),
        candidate_sha256=next(a.sha256 for a in bundle.candidate.artifacts if a.role=='source'),
        candidate_artifact_ids=sorted(a.artifact_id for a in bundle.candidate.artifacts),
        native_candidate_digest=bundle.candidate.content_digest,bundle_digest=bundle.content_digest,
        policy_sha256=policy.content_digest,policy_id=label(policy.policy_id),policy_version=label(policy.policy_version),
        as_of=count(report.as_of,2**53-1),native_release_status=report.release_status,ready_for_review=report.ready_for_review,
        blocking_gates=blocked,global_reasons=reasons,gates=sorted(rows,key=lambda g:g['gate_id']),
        artifact_checks=[dict(artifact_id=label(a.artifact_id),status=label(a.status),diagnostic=label(a.diagnostic),
            expected_sha256=hash_value(a.expected_sha256),actual_sha256=hash_value(a.actual_sha256) if a.actual_sha256 else None,
            bytes_read=count(a.bytes_read,256*1024*1024)) for a in report.artifact_checks],
        historical_decision=True,current_deployment_authority=False,release_authorized=False,product_accepted=False)
    safe_tree(result);return result

def repair_projection(export,plan,snapshot,policy,receipts):
    """Validate native journal/attempt correspondence; never accept a UI history."""
    require(type(plan) is RepairPlan and type(snapshot) is Snapshot and type(policy) is RepairPolicy,
        'native_repair_context_required',400)
    require((plan.snapshot_digest,plan.policy_digest)==(snapshot.content_digest,policy.content_digest),
        'repair_context_binding',400)
    shape(export,('binding','events','chain_head','product_accepted'))
    require(export['product_accepted'] is False,'repair_unauthorized_promotion',400)
    binding=dict(run_id=snapshot.run_id,revision=snapshot.revision,snapshot_digest=snapshot.content_digest,policy_digest=policy.content_digest)
    require(export['binding']==binding,'repair_context_binding',400)
    events=export['events'];require(type(events) is list and len(events)<=2*policy.max_attempts,'repair_history_limit',413)
    require(type(receipts) is tuple and len(receipts)<=policy.max_attempts and all(type(r) is dict for r in receipts),
        'repair_receipts_invalid',400)
    indexed={count(r.get('attempt'),20):r for r in receipts};require(len(indexed)==len(receipts),'repair_duplicate_receipt',400)
    claims={};finished={}
    for event in events:
        require(type(event) is dict and event.get('kind') in ('RESERVED','FINISHED'),'repair_journal_event_invalid',400)
        n=count(event.get('attempt'),20);require(n>0,'repair_journal_event_invalid',400)
        if event['kind']=='RESERVED':
            require(n==len(claims)+1 and n not in claims,'repair_journal_event_invalid',400)
            claims[n]=event
        else:
            require(n in claims and n not in finished and event.get('status') in ('REJECTED','STAGED_FOR_REVIEW'),
                'repair_journal_event_invalid',400);finished[n]=event
    require(set(indexed)==set(finished),'repair_receipt_inventory',400)
    attempts=[]
    for n,claim in sorted(claims.items()):
        row=dict(attempt=n,proposal_id=label(claim['proposal_id']),proposal_digest=hash_value(claim['proposal_digest']),
            effect_digest=hash_value(claim['effect_digest']),reserved_at=count(claim['reserved_at'],2**53-1),
            reserved_bytes=count(claim['reserved_bytes'],policy.max_total_replacement_bytes),
            status='REVIEW_REQUIRED',reason='unfinished_reservation_manual_review',required_checks=[],checks=[],
            candidate_digest=None,receipt_digest=None,remaining_failure_ids=[],worker_executed=False)
        if n in finished:
            r=indexed[n];d=hash_value(r['receipt_digest'])
            require(native_digest({k:v for k,v in r.items() if k not in ('receipt_digest','journal_head')})==d and
                finished[n]['receipt_digest']==d,'repair_receipt_integrity',400)
            require(r['schema_version']=='bie.qa.repair-attempt/1' and r['status']==finished[n]['status'] and
                (r['proposal_id'],r['proposal_digest'],r['base_digest'],r['policy_digest'],r['plan_digest'])==
                (claim['proposal_id'],claim['proposal_digest'],snapshot.content_digest,policy.content_digest,plan.content_digest),
                'repair_receipt_binding',400)
            require(r['product_accepted'] is False and r['canonical_repository_modified'] is False and
                r['original_files_written'] is False and r['downstream_previous_evidence_reusable'] is False,
                'repair_unauthorized_promotion',400)
            require(type(r['worker_executed']) is bool,'repair_receipt_invalid',400)
            required=codes(r['required_checks']);require(len(set(required))==len(required) and set(required)<={c.check_id for c in policy.checks},
                'repair_checks_invalid',400)
            checks=[]
            for item in r['outcomes']:
                try:outcome=CheckOutcome(**dict(item,diagnostics=tuple(item['diagnostics'])))
                except (ContractError,TypeError,KeyError):raise OperatorError('repair_checks_invalid',400) from None
                require(outcome.check_id in required and outcome.policy_digest==policy.content_digest and
                    outcome.candidate_digest==r['candidate_digest'],'repair_checks_invalid',400)
                checks.append(dict(check_id=outcome.check_id,status=outcome.status,diagnostics=codes(outcome.diagnostics),
                    witness_digest=outcome.witness_digest))
            require(len({c['check_id'] for c in checks})==len(checks),'repair_checks_invalid',400)
            if r['status']=='STAGED_FOR_REVIEW':
                require(plan.authenticated and not plan.diagnostics and r['worker_executed'] and required and
                    set(required)=={c['check_id'] for c in checks} and
                    all(c['status']=='PASS' for c in checks) and not r['diagnostics'] and r['candidate'],
                    'repair_staged_without_checks',400)
            if r['candidate'] is not None:
                from bie.qa.release_v2.contracts import ArtifactRef
                try:
                    candidate=Snapshot(r['candidate']['run_id'],r['candidate']['revision'],
                        tuple(ArtifactRef(**a) for a in r['candidate']['artifacts']))
                except (ContractError,TypeError,KeyError):raise OperatorError('repair_candidate_invalid',400) from None
                require(candidate.content_digest==r['candidate_digest'] and (candidate.run_id,candidate.revision)==
                    (snapshot.run_id,snapshot.revision),'repair_candidate_invalid',400)
            else:require(not r['candidate_digest'],'repair_candidate_invalid',400)
            row.update(status=r['status'],reason=None,diagnostics=codes(r['diagnostics']),required_checks=required,
                checks=checks,candidate_digest=r['candidate_digest'] or None,receipt_digest=d,
                invalidated_previous_checks=codes(r['invalidated_previous_checks']),
                remaining_failure_ids=codes(r['remaining_failure_ids']),worker_executed=r['worker_executed'])
        attempts.append(row)
    result=dict(attempt_id='repair-'+hash_value(native_digest(export)),candidate_sha256=snapshot.artifacts[0].sha256,
        candidate_artifact_ids=sorted(a.artifact_id for a in snapshot.artifacts),
        snapshot_digest=snapshot.content_digest,policy_sha256=policy.content_digest,plan_digest=plan.content_digest,
        journal_chain_head=hash_value(export['chain_head']),plan_status=plan.status,authenticated_inventory=plan.authenticated,
        inventory_reasons=codes(plan.diagnostics),defects=[dict(failure_id=label(f.failure_id),task_id=label(f.task_id),code=label(f.code),
            owner=label(f.owner),severity=f.severity,category=f.category,automatic=f.automatic,
            report_sha256=hash_value(f.report_sha256)) for f in plan.failures],attempts=attempts,
        automatic_retry=False,repository_write_permitted=False,historical_decision=True,current_deployment_authority=False,
        release_authorized=False,product_accepted=False)
    safe_tree(result);return result

class Assurance(Quality):
    def _verify_refs(self,p,run,refs,origin):
        with self.art.context(p,run,'publish') as (db,body,native):
            require(all(r.artifact_id for r in refs),'assurance_candidate_binding',400)
            inventory=self.art.inventory(db,body,native);api=self.art.canonical_api(inventory,native)
            for ref in refs:
                r=inventory.get(ref.artifact_id)
                require(r is not None and (ref.sha256,ref.size)==(r.blob_digest,r.blob_size),'assurance_candidate_binding',400)
                require(r.metadata.get('evidence_origin')!='SYNTHETIC_TEST' or origin=='SYNTHETIC_TEST',
                    'assurance_fixture_promotion',400)
                api.content(ref.artifact_id)
            return body

    def bind_gates(self,p,run,evaluator,bundle,artifact_root,*,as_of,evidence_origin):
        self.s.authorize(p,'publish')
        require(type(evaluator) is ReleaseEvaluator and type(bundle) is EvidenceBundle,'native_gate_evaluator_required',400)
        require(len(bundle.candidate.artifacts)<=128 and len(bundle.evidence)<=128,'gate_evidence_limit',413)
        refs=bundle.candidate.artifacts;body=self._verify_refs(p,run,refs,evidence_origin)
        source=[r for r in refs if r.role=='source'];require(len(source)==1 and
            source[0].artifact_id=='source-'+body['native_job_id'][4:] and source[0].sha256==body['source_hash'] and
            bundle.candidate.run_id==body['native_job_id'],'assurance_run_binding',400)
        try:report=ReleaseEvaluator.evaluate(evaluator,bundle,artifact_root,as_of=as_of)
        except ContractError:raise OperatorError('native_gate_evaluation_failed',400) from None
        view=gate_projection(report,bundle,evaluator.policy)
        return self._bind(p,run,source[0].artifact_id,'gates',view['attempt_id'],view,native_digest(report.to_dict()),evidence_origin,
            parent_refs=tuple(r.artifact_id for r in refs))

    def bind_repairs(self,p,run,journal,plan,receipts,*,evidence_origin):
        self.s.authorize(p,'publish');require(type(journal) is Journal,'native_repair_journal_required',400)
        snapshot,policy=journal.snapshot,journal.policy;body=self._verify_refs(p,run,snapshot.artifacts,evidence_origin)
        source='source-'+body['native_job_id'][4:]
        require(snapshot.run_id==body['native_job_id'] and snapshot.artifacts[0].artifact_id==source and
            snapshot.artifacts[0].sha256==body['source_hash'],'assurance_run_binding',400)
        try:export=Journal.export(journal)
        except ContractError:raise OperatorError('native_repair_journal_invalid',400) from None
        view=repair_projection(export,plan,snapshot,policy,receipts)
        return self._bind(p,run,source,'repairs',view['attempt_id'],view,native_digest(export),evidence_origin,
            parent_refs=tuple(r.artifact_id for r in snapshot.artifacts))

    def _item(self,db,body,native,records,aid):
        r=records[aid];require(r.artifact_type in ('operator.quality.gates','operator.quality.repairs') and r.blob_size<=MAX_RECORD,
            'assurance_artifact_invalid')
        wire=strict_json(self.art.canonical_api(records,native).content(aid),MAX_RECORD)
        shape(wire,('schema','kind','source_hash','run_id','candidate_id','receipt_sha256','evidence_origin','view'))
        require(wire['schema']=='bie.operator.quality/1' and wire['kind'] in KINDS and wire['source_hash']==body['source_hash'] and
            wire['run_id']==body['run_id'] and r.artifact_type=='operator.quality.'+wire['kind'],'assurance_source_mismatch')
        require(wire['candidate_id'] in r.parent_artifact_ids and wire['view']['candidate_sha256']==body['source_hash'],
            'assurance_parent_binding')
        require(set(wire['view']['candidate_artifact_ids'])<=set(r.parent_artifact_ids),'assurance_parent_binding')
        for ref in r.parent_artifact_ids:self.art.canonical_api(records,native).content(ref)
        safe_tree(wire['view']);hash_value(wire['receipt_sha256'])
        require(wire['view']['product_accepted'] is False and wire['view']['release_authorized'] is False and
            wire['view']['current_deployment_authority'] is False,'assurance_unauthorized_promotion')
        require(wire['evidence_origin'] in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'assurance_origin_invalid')
        return dict(artifact_id=aid,sha256=r.blob_digest,receipt_sha256=wire['receipt_sha256'],view=wire['view'],
            evidence_origin=wire['evidence_origin'],fixture_evidence=wire['evidence_origin']=='SYNTHETIC_TEST',
            integrity='VERIFIED',signature_verified=False,privileged_storage_rewrite_protected=False,
            historical_snapshot=True,current_deployment_authority=False,product_accepted=False,release_authorized=False)

    def get(self,p,run,kind,offset=0,limit=10):
        require(kind in KINDS,'assurance_kind_unavailable',404);pagination(offset,limit)
        with self.art.context(p,run) as (db,body,native):
            records=self.art.inventory(db,body,native)
            rows=db.execute('SELECT artifact FROM graphs WHERE run=? AND kind LIKE ? ORDER BY kind',
                (run,'artifact:quality:'+kind+':%')).fetchall()
            require(len(rows)<=MAX_HISTORY,'quality_history_limit',429)
            result=dict(kind=kind,status='AVAILABLE' if rows else 'NOT_RUN',reason=None if rows else
                ('native_product_candidate_not_bound' if kind=='gates' else 'native_repair_journal_not_bound'),
                total=len(rows),items=[self._item(db,body,native,records,r['artifact']) for r in rows[offset:offset+limit]],
                next_offset=offset+limit if len(rows)>offset+limit else None,product_accepted=False,release_authorized=False)
            if kind=='gates' and not rows:
                result['required_gates']=[dict(gate_id=g.gate_id,owner=g.owner,status='NOT_RUN',
                    reason='no_evaluated_product_candidate') for g in enterprise_policy().gates]
            return result
