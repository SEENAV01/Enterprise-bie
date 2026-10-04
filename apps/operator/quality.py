"""Read-only product projections of verified Section17 persisted decisions.

Trusted Python producer ports accept native ledgers, never UI supplied scores.
The operator CAS freezes safe historical snapshots; it is not a replacement
evaluator, release authority, or externally attested audit system.
"""
from dataclasses import asdict
from fractions import Fraction
from bie.evaluation.benchmarks.anti_gaming import AttemptLedger
from bie.evaluation.benchmarks.versioning import Snapshot
from bie.evaluation.benchmarks.release.ledger import ReleaseLedger
from bie.evaluation.benchmarks.models import BenchmarkError, digest as native_digest
from bie.infrastructure.persistence import PersistedArtifactRecord
from .artifacts import ProductArtifacts,pagination,MAX_ARTIFACTS
from .contracts import canonical,digest,require,strict_json,HASH,OperatorError
from .view_contracts import ident,shape

KINDS=('benchmark','release')
MAX_RECORD=256*1024
MAX_HISTORY=128

def label(value):
    require(type(value) is str and 0<len(value)<=160 and all(c.isascii() and (c.isalnum() or c in '._-:') for c in value),
            'quality_identity_invalid',400)
    return value

def hash_value(value):
    require(type(value) is str and HASH.fullmatch(value),'quality_digest_invalid',400);return value

def count(value,maximum=10000):
    require(type(value) is int and 0<=value<=maximum,'quality_count_invalid',400);return value

def ratio(value,signed=False):
    require(type(value) in (str,int,float) and not isinstance(value,bool),'quality_ratio_invalid',400)
    require(len(str(value))<=64,'quality_ratio_invalid',400)
    try:r=Fraction(str(value))
    except (ValueError,ZeroDivisionError,OverflowError):raise OperatorError('quality_ratio_invalid',400) from None
    require((-1 if signed else 0)<=r<=1,'quality_ratio_invalid',400)
    return str(r)

def codes(values):
    require(type(values) in (list,tuple) and len(values)<=512,'quality_reasons_invalid',400)
    return [label(v) for v in values]

def benchmark_projection(report,snapshot):
    # Independently enforce frozen denominator and status, even when stored native
    # JSON is accidentally changed alongside its checksum. No answers/golden text.
    shape(report,('binding','denominator','received_count','passed_count','score','missing_case_ids','results','status',
                  'release_authorized','product_accepted'))
    b=report['binding'];shape(b,('run_id','campaign_id','candidate_sha256','policy_sha256','dataset_sha256','split'))
    for k in ('run_id','campaign_id'):label(b[k])
    for k in ('candidate_sha256','policy_sha256','dataset_sha256'):hash_value(b[k])
    require(b['split'] in ('DEVELOPMENT','CALIBRATION','HOLDOUT'),'quality_split_invalid',400)
    require(b['dataset_sha256']==snapshot.sha256,'quality_dataset_mismatch',400)
    roster=sorted(c.case_id for c in snapshot.cases if c.split==b['split'])
    require(0<len(roster)<=512,'quality_case_limit',413)
    rows=report['results'];require(type(rows) is list and len(rows)<=len(roster),'quality_results_invalid',400)
    seen=set();safe=[]
    cases={c.case_id:c for c in snapshot.cases}
    for r in rows:
        shape(r,('case_id','status','evidence_sha256'));key=label(r['case_id'])
        require(key in roster and key not in seen,'quality_roster_invalid',400);seen.add(key)
        require(r['status'] in ('PASS','FAIL','ERROR','ABSTAIN'),'quality_status_invalid',400)
        safe.append(dict(case_id=key,status=r['status'],evidence_sha256=hash_value(r['evidence_sha256']),
                         task_id=cases[key].task_id,domain=cases[key].domain))
    den=count(report['denominator'],512);passed=count(report['passed_count'],512)
    missing=sorted(set(roster)-seen)
    received=count(report['received_count'],512)
    require(den==len(roster) and received==len(rows) and passed==sum(r['status']=='PASS' for r in rows)
            and report['missing_case_ids']==missing and ratio(report['score'])==ratio(passed/den),
            'quality_denominator_invalid',400)
    require(report['status']==('PASS' if not missing and passed==den else 'FAIL'),'quality_status_invalid',400)
    require(report['release_authorized'] is False and report['product_accepted'] is False,'quality_unauthorized_promotion',400)
    return dict(attempt_id=b['run_id'],campaign_id=b['campaign_id'],status=report['status'],
        candidate_sha256=b['candidate_sha256'],policy_sha256=b['policy_sha256'],dataset=snapshot.public_manifest(),split=b['split'],
        denominator=den,received_count=len(rows),passed_count=passed,score=ratio(report['score']),
        measured_coverage=ratio(len(rows)/den),missing_case_ids=missing,cases=sorted(safe,key=lambda r:r['case_id']),
        evaluator_type='CANONICAL_ATTEMPT_LEDGER_RESULTS',native_bie_execution_verified=False,
        live_assessor_status='NOT_RUN',golden_benchmark_certified=False,release_authorized=False,product_accepted=False)

def release_projection(receipt,manifest,policy):
    require(receipt['manifest_sha256']==native_digest(manifest) and receipt['policy_sha256']==native_digest(policy),
            'quality_release_pins_mismatch',400)
    r=receipt['report'];require(r.get('product_accepted') is False and r.get('release_authorized') is False,
                              'quality_unauthorized_promotion',400)
    require(r.get('outcome') in ('BLOCKED','DIAGNOSTIC_PASS','PASS'),'quality_status_invalid',400)
    if 'report_sha256' in r:
        require(native_digest({k:v for k,v in r.items() if k!='report_sha256'})==r['report_sha256'],'quality_report_integrity',400)
    else:require(r['outcome']=='BLOCKED','quality_report_integrity',400)
    # Only native allowlisted summaries are exposed; no source, rationale, secret,
    # signature, assessment answer or arbitrary exception strings are serialized.
    result=dict(attempt_id=label(receipt['attempt_id']),campaign_id=label(receipt['campaign_id']),
        candidate_sha256=hash_value(receipt['artifact_sha256']),policy_sha256=hash_value(receipt['policy_sha256']),
        manifest_sha256=hash_value(receipt['manifest_sha256']),inputs_sha256=hash_value(receipt['inputs_sha256']),
        outcome=r['outcome'],mode=policy['mode'],reasons=codes(r['reasons']),
        benchmark_gate_passed=r.get('benchmark_gate_passed') is True,release_authorized=False,product_accepted=False,
        historical_decision=True,current_deployment_authority=False,policy_version=label(policy['version']),
        dataset_sha256=hash_value(manifest['dataset_sha256']),benchmark_id=label(manifest['id']),
        benchmark_version=label(manifest['version']),evaluated_at=count(r.get('evaluated_at',0),2**53-1),
        reference_grade=label(manifest['reference_grade']),split=label(manifest['split']),
        metric_rows=[],critical_floors=[],domain_floors=[],agreement=[],coverage=[],raters=[])
    for x in r.get('metric_rows',[]):
        result['metric_rows'].append(dict(metric_id=label(x['id']),status=label(x['status']),score=ratio(x['score'])))
    for x in policy.get('critical_floors',{}).get('floors',[]):
        result['critical_floors'].append(dict(metric_id=label(x['id']),minimum=ratio(x['minimum'])))
    for x in policy.get('domains',{}).get('domains',[]):
        result['domain_floors'].append(dict(domain=label(x['id']),minimum_score=ratio(x['minimum_score']),
            minimum_cases=count(x['minimum_cases']),minimum_measured_fraction=ratio(x['minimum_measured_fraction'])))
    for x in r.get('agreement',{}).get('pairs',[]):
        result['agreement'].append(dict(pair=' / '.join(label(v) for v in x['assessors']),
            paired_count=count(x['paired_count']),expected_count=count(x['expected_count']),
            observed_agreement=None if x['observed_agreement'] is None else ratio(x['observed_agreement']),
            mean_absolute_score_difference=None if x['mean_absolute_score_difference'] is None else ratio(x['mean_absolute_score_difference']),
            kappa=None if x['kappa'] is None else ratio(x['kappa'],signed=True),kappa_state=label(x['kappa_state'])))
    for key in ('enterprise','critical_floors','domain_minimums','agreement'):
        sub=r.get(key,{})
        result['coverage'].append(dict(gate=key,status=label(sub.get('outcome',sub.get('status','NOT_RUN'))),reasons=codes(sub.get('reasons',[]))))
    for x in policy.get('aggregation',{}).get('raters',[]):
        result['raters'].append(dict(id=label(x['id']),kind=label(x['kind']),independence_group=label(x['independence_group'])))
    safe_tree(result)
    return result

def safe_tree(value,depth=0):
    require(depth<=12,'quality_depth_limit',413)
    if type(value) is dict:
        require(len(value)<=100,'quality_collection_limit',413)
        for k,v in value.items():label(k);safe_tree(v,depth+1)
    elif type(value) is list:
        require(len(value)<=512,'quality_collection_limit',413)
        for v in value:safe_tree(v,depth+1)
    elif type(value) is str:
        require(len(value)<=200 and all(ord(c)>=32 for c in value),'quality_text_invalid',400)
    else:require(value is None or type(value) in (int,float,bool),'quality_type_invalid',400)

class Quality:
    def __init__(self,service):self.s=service;self.art=ProductArtifacts(service)

    def bind_benchmark(self,p,run_id,candidate_id,ledger,attempt_id,snapshot,*,evidence_origin):
        self.s.authorize(p,'publish')
        require(type(ledger) is AttemptLedger and type(snapshot) is Snapshot,'native_ledger_required',400)
        try:report=AttemptLedger.get_report(ledger,attempt_id)
        except BenchmarkError:raise OperatorError('native_benchmark_receipt_invalid',400) from None
        view=benchmark_projection(report,snapshot)
        return self._bind(p,run_id,candidate_id,'benchmark',attempt_id,view,native_digest(report),evidence_origin)

    def bind_release(self,p,run_id,candidate_id,ledger,attempt_id,manifest,policy,*,evidence_origin):
        self.s.authorize(p,'publish');require(type(ledger) is ReleaseLedger,'native_ledger_required',400)
        try:receipt=ReleaseLedger.get(ledger,attempt_id)
        except BenchmarkError:raise OperatorError('native_release_receipt_invalid',400) from None
        view=release_projection(receipt,manifest,policy)
        # Every evaluated context must be bound to the real selected native run
        # and candidate, not merely the manifest's aggregate artifact hash.
        with self.art.context(p,run_id) as (_,body,_native):
            require(all(c['context']['run_id']==body['native_job_id'] and
                        c['context']['candidate_sha256']==view['candidate_sha256'] for c in manifest['cases']),
                    'quality_run_binding_mismatch',400)
        return self._bind(p,run_id,candidate_id,'release',attempt_id,view,native_digest(receipt),evidence_origin)

    def _bind(self,p,run_id,candidate_id,kind,attempt_id,view,receipt_hash,origin,*,parent_refs=()):
        label(attempt_id);ident(candidate_id);hash_value(receipt_hash)
        require(origin in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'invalid_evidence_origin',400)
        with self.art.context(p,run_id,'publish') as (db,body,native):
            records=self.art.inventory(db,body,native);candidate=records.get(candidate_id)
            require(candidate is not None,'quality_candidate_missing',400)
            require(candidate.blob_digest==view['candidate_sha256'],'quality_candidate_mismatch',400)
            if kind=='benchmark':require(view['attempt_id']==body['native_job_id'],'quality_run_binding_mismatch',400)
            require(type(parent_refs) in (tuple,list) and len(parent_refs)<=128,'artifact_parent_limit',400)
            parents=sorted({candidate_id,'source-'+body['native_job_id'][4:]}|set(parent_refs))
            for ref in parents:ident(ref);require(ref in records,'artifact_parent_invalid',400)
            for ref in parents:self.art.canonical_api(records,native).content(ref)
            key='artifact:quality:'+kind+':'+attempt_id
            wire=dict(schema='bie.operator.quality/1',kind=kind,source_hash=body['source_hash'],run_id=run_id,
                candidate_id=candidate_id,receipt_sha256=receipt_hash,evidence_origin=origin,view=view)
            raw=canonical(wire);require(len(raw)<=MAX_RECORD,'quality_size_limit',413)
            old=db.execute('SELECT artifact FROM graphs WHERE run=? AND kind=?',(run_id,key)).fetchone()
            if old:
                require(self.art.canonical_api(records,native).content(old['artifact'])==raw,'quality_immutable_conflict',409)
                return self._item(db,body,native,records,old['artifact'])
            require(db.execute("SELECT COUNT(*) FROM graphs WHERE run=? AND kind LIKE 'artifact:quality:%'",(run_id,)).fetchone()[0]<MAX_HISTORY,
                    'quality_history_limit',429)
            require(len(records)<MAX_ARTIFACTS,'artifact_inventory_limit',429)
            blob=native.cas.put_bytes(raw);aid='opquality-'+digest(dict(run=run_id,kind=kind,attempt=attempt_id,sha=blob.digest))
            rec=PersistedArtifactRecord(aid,'operator.quality.'+kind,'sha256',blob.digest,blob.size,body['native_job_id'],
                'EVAL',True,dict(evidence_origin=origin,source_hash=body['source_hash']),parents)
            if aid in records:require(asdict(records[aid])==asdict(rec),'artifact_record_tampered')
            else:native.persistence.register_artifact(rec)
            db.execute('INSERT INTO graphs VALUES(?,?,?,?)',(run_id,key,aid,digest(asdict(rec))))
            self.s.catalog.event(db,p.actor,'QUALITY_RECEIPT_BOUND',run_id,dict(kind=kind,artifact_id=aid,receipt_sha256=receipt_hash))
            records=self.art.inventory(db,body,native)
            return self._item(db,body,native,records,aid)

    def _item(self,db,body,native,records,aid):
        r=records[aid];require(r.artifact_type in ('operator.quality.benchmark','operator.quality.release') and r.blob_size<=MAX_RECORD,
                              'quality_artifact_invalid')
        raw=self.art.canonical_api(records,native).content(aid);wire=strict_json(raw,MAX_RECORD)
        shape(wire,('schema','kind','source_hash','run_id','candidate_id','receipt_sha256','evidence_origin','view'))
        require(wire['schema']=='bie.operator.quality/1' and wire['source_hash']==body['source_hash'] and wire['run_id']==body['run_id']
            and r.artifact_type=='operator.quality.'+wire['kind'],'quality_source_mismatch')
        require(wire['candidate_id'] in r.parent_artifact_ids and records[wire['candidate_id']].blob_digest==wire['view']['candidate_sha256'],
                'quality_parent_binding_invalid')
        hash_value(wire['receipt_sha256']);safe_tree(wire['view'])
        require(wire['view']['product_accepted'] is False and wire['view']['release_authorized'] is False,'quality_unauthorized_promotion')
        require(wire['evidence_origin'] in ('SYNTHETIC_TEST','NATIVE_PRODUCER'),'quality_origin_invalid')
        for ref in r.parent_artifact_ids:self.art.canonical_api(records,native).content(ref)
        return dict(artifact_id=aid,sha256=r.blob_digest,receipt_sha256=wire['receipt_sha256'],candidate_id=wire['candidate_id'],
            evidence_origin=wire['evidence_origin'],fixture_evidence=wire['evidence_origin']=='SYNTHETIC_TEST',
            view=wire['view'],integrity='VERIFIED',historical_snapshot=True,signature_verified=False,
            privileged_storage_rewrite_protected=False,product_accepted=False,release_authorized=False)

    def get(self,p,run_id,kind,offset=0,limit=10):
        require(kind in KINDS,'quality_kind_unavailable',404);pagination(offset,limit)
        with self.art.context(p,run_id) as (db,body,native):
            rows=db.execute('SELECT artifact FROM graphs WHERE run=? AND kind LIKE ? ORDER BY kind',(run_id,'artifact:quality:'+kind+':%')).fetchall()
            require(len(rows)<=MAX_HISTORY,'quality_history_limit',429)
            records=self.art.inventory(db,body,native)
            return dict(kind=kind,status='AVAILABLE' if rows else 'NOT_RUN',reason=None if rows else 'native_quality_receipt_not_bound',
                items=[self._item(db,body,native,records,r['artifact']) for r in rows[offset:offset+limit]],total=len(rows),
                next_offset=offset+limit if len(rows)>offset+limit else None,product_accepted=False,release_authorized=False)
