from __future__ import annotations
from dataclasses import asdict
import hashlib,json
from pathlib import Path
from bie.bie_core.artifact_contracts import ArtifactRef,ProvenanceSource
from ..canonical import fingerprint
from ..build_runtime_engine.pipeline import build_runtime_package
from .contracts import EnterpriseSessionRequest,EnterpriseSessionResult,MasteryRecord
from .durable_store import DurableGameStore
from .telemetry import GovernedTelemetrySink
from .mastery import PersistentMasteryStore
from .canonical_bindings import verify_canonical_bindings
from .errors import GameOperationsError

def _source_provenance(document):
    return [ProvenanceSource(r.artifact_id,{'locator':r.locator,'role':r.role},'sha256:'+r.content_sha256) for r in document.provenance.refs]
def _artifact_ref(store,artifact_id):
    env=json.loads(store.catalog.read_artifact(artifact_id))
    return ArtifactRef(env['artifact_id'],env['artifact_type'],env['schema_version'],env['content_hash'])
def _artifact_payload(store,artifact_id):
    return json.loads(store.catalog.read_artifact(artifact_id))['payload']
def _request_fp(ctx,asset_blobs,req):
    return fingerprint({'compiler':fingerprint(ctx),'assets':tuple((k,hashlib.sha256(v).hexdigest()) for k,v in sorted(asset_blobs.items())),'run_id':req.run_context.run_id,'session_id':req.session_id,'learner':req.learner_key_hash,'outcomes':req.outcomes,'consent':req.consent})
def _telemetry_event(ctx,outcome):
    matches=[(g,l) for g in ctx.document.experiences for l in g.levels for ch in l.challenges if ch.challenge_id==outcome.challenge_id and ch.learning.objective_id==outcome.objective_id and (outcome.game_id is None or (outcome.game_id==g.game_id and outcome.level_id==l.level_id))]
    if len(matches)!=1:raise GameOperationsError('GAME_OPS_OUTCOME_SCOPE_AMBIGUOUS_OR_MISSING')
    game,level=matches[0]
    return {'event':outcome.event_type,'game_id':game.game_id,'level_id':level.level_id,'challenge_id':outcome.challenge_id,'attempt_number':outcome.attempt_number,'outcome_code':outcome.outcome_code,'mechanic_id':outcome.mechanic_id,'objective_id':outcome.objective_id,'adaptation_id':outcome.adaptation_ids[0] if outcome.adaptation_ids else ''}
def _target(document,objective_id):
    for exp in document.experiences:
        for level in exp.levels:
            for ch in level.challenges:
                if ch.learning.objective_id==objective_id:return ch.learning.mastery_target,bool(ch.learning.misconception_ids)
    raise GameOperationsError('GAME_OPS_OBJECTIVE_NOT_IN_DOCUMENT')
def _result_from_payload(run_id,session_id,result_id,payload,idempotent,resumed):
    mastery=tuple(MasteryRecord(**x).validate() for x in payload['mastery'])
    return EnterpriseSessionResult(run_id,session_id,result_id,payload['build_artifact_id'],payload.get('telemetry_artifact_id'),payload['learning_artifact_id'],mastery,tuple(tuple(x) for x in payload['adaptation_actions']),idempotent,resumed,False).validate()

def run_enterprise_session(ctx,asset_blobs,root:Path,request:EnterpriseSessionRequest,build_policy=None,fail_after_checkpoint:str|None=None):
    ctx.validate();request.validate()
    for outcome in request.outcomes:_telemetry_event(ctx,outcome)
    verify_canonical_bindings(Path(__file__).resolve().parents[3])
    store=DurableGameStore(Path(root)/'operations');fp=_request_fp(ctx,asset_blobs,request)
    job=store.begin_job(request.idempotency_key,fp,request.run_context.run_id,request.session_id,request.owner)
    try:
        if job['idempotent']:
            payload=_artifact_payload(store,job['result_ref'])
            return _result_from_payload(request.run_context.run_id,request.session_id,job['result_ref'],payload,True,False)
        cp=dict(job['checkpoint'])
        if 'source_artifact_id' not in cp:
            src=store.source_envelope(request.run_context.run_id,ctx.document.fingerprint(),ctx.document.provenance.refs)
            src_ref=store.put_envelope(src,'BIE-GAME-OPS-SOURCE')
            cp=store.checkpoint(request.idempotency_key,'source_artifact_id',src_ref.artifact_id)
        source_ref=_artifact_ref(store,cp['source_artifact_id'])
        if 'build_artifact_id' not in cp:
            kwargs={} if build_policy is None else {'policy':build_policy}
            runtime=build_runtime_package(ctx,asset_blobs,Path(root)/'runtime',**kwargs)
            _,bref=store.derive('game.runtime.package',request.run_context.run_id,[source_ref],{'package_fingerprint':runtime.manifest.package_fingerprint,'compiler_bundle_fingerprint':runtime.manifest.compiler_bundle_fingerprint,'build_receipts':[r.receipt_id for r in runtime.receipts]},'BIE-GAME-OPS-BUILD',_source_provenance(ctx.document),{'session_id':request.session_id},False)
            cp=store.checkpoint(request.idempotency_key,'build_artifact_id',bref.artifact_id)
            if fail_after_checkpoint=='build':raise GameOperationsError('GAME_OPS_INJECTED_CRASH_AFTER_BUILD')
        build_ref=_artifact_ref(store,cp['build_artifact_id'])
        tele=GovernedTelemetrySink(store.db);mastery_store=PersistentMasteryStore(store.db)
        # Persist telemetry once. Consent-disabled sessions intentionally produce no telemetry artifact.
        if 'telemetry_processed' not in cp:
            tele_rows=[]
            for outcome in request.outcomes:
                tr=tele.record(request.session_id,_telemetry_event(ctx,outcome),request.consent,ctx.telemetry_allowlist,event_key=fingerprint(_telemetry_event(ctx,outcome)))
                if tr:tele_rows.append(tr)
            if tele_rows:
                _,tref=store.derive('game.telemetry.events',request.run_context.run_id,[build_ref],{'session_id':request.session_id,'events':tele_rows,'raw_text':False,'consent_policy':request.consent.policy_id},'BIE-GAME-OPS-TELEMETRY',_source_provenance(ctx.document),{'retention_days':request.consent.retention_days},True)
                cp=store.checkpoint(request.idempotency_key,'telemetry_artifact_id',tref.artifact_id)
            cp=store.checkpoint(request.idempotency_key,'telemetry_processed',True)
        tele_rows=tele.export(request.session_id)
        tele_by_attempt={(r['payload']['challenge_id'],r['payload']['attempt_number']):r for r in tele_rows}
        if 'learning_artifact_id' not in cp:
            mastery_rows=[];adapt=[]
            for outcome in request.outcomes:
                tr=tele_by_attempt.get((outcome.challenge_id,outcome.attempt_number))
                eid='learning:'+hashlib.sha256((request.session_id+'|'+fingerprint({'game_id':_telemetry_event(ctx,outcome)['game_id'],'level_id':_telemetry_event(ctx,outcome)['level_id'],'challenge_id':outcome.challenge_id,'attempt':outcome.attempt_number})).encode()).hexdigest()[:24]
                rec=mastery_store.update(request.learner_key_hash,outcome.objective_id,outcome.outcome_code,outcome.mastery_weight,outcome.evidence_strength,eid);mastery_rows.append(rec)
                target,mis=_target(ctx.document,outcome.objective_id);adapt.append((outcome.objective_id,mastery_store.adaptation_for(rec,target,mis)))
            by={r.objective_id:r for r in mastery_rows};mastery_rows=tuple(by[k] for k in sorted(by))
            _,lref=store.derive('game.learning.state',request.run_context.run_id,[build_ref],{'learner_key_hash':request.learner_key_hash,'mastery':[asdict(x) for x in mastery_rows],'adaptation_actions':[list(x) for x in adapt]},'BIE-GAME-OPS-LEARNING',_source_provenance(ctx.document),{'persistent':True},True)
            cp=store.checkpoint(request.idempotency_key,'learning_artifact_id',lref.artifact_id)
            if fail_after_checkpoint=='learning':raise GameOperationsError('GAME_OPS_INJECTED_CRASH_AFTER_LEARNING')
        learning_payload=_artifact_payload(store,cp['learning_artifact_id']);mastery_rows=tuple(MasteryRecord(**x).validate() for x in learning_payload['mastery']);adapt=tuple(tuple(x) for x in learning_payload['adaptation_actions'])
        parents=[build_ref,_artifact_ref(store,cp['learning_artifact_id'])]
        telemetry_id=cp.get('telemetry_artifact_id')
        if telemetry_id:parents.append(_artifact_ref(store,telemetry_id))
        payload={'session_id':request.session_id,'build_artifact_id':cp['build_artifact_id'],'telemetry_artifact_id':telemetry_id,'learning_artifact_id':cp['learning_artifact_id'],'mastery':[asdict(x) for x in mastery_rows],'adaptation_actions':[list(x) for x in adapt],'idempotency_key':request.idempotency_key}
        if 'result_artifact_id' not in cp:
            _,rref=store.derive('game.session.result',request.run_context.run_id,parents,payload,'BIE-GAME-OPS-SESSION',_source_provenance(ctx.document),{'idempotent':True,'product_accepted':False},True)
            cp=store.checkpoint(request.idempotency_key,'result_artifact_id',rref.artifact_id)
        result_id=cp['result_artifact_id'];store.complete(request.idempotency_key,request.owner,result_id)
        return _result_from_payload(request.run_context.run_id,request.session_id,result_id,payload,False,job['resumed'])
    finally:
        store.close()

def load_persisted_mastery_signals(root:Path,document,learner_key_hash:str):
    store=DurableGameStore(Path(root)/'operations')
    try:return PersistentMasteryStore(store.db).signals_for(document,learner_key_hash)
    finally:store.close()
