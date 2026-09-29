"""H1 regression controls. Every key, approval and subject here is SYNTHETIC.
No native book/media or production certificate is created by these tests.
"""
from pathlib import Path
import sys,json,unittest,hashlib
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qa_publication22'))
from pub22_support import Case, Fixture, ref, NOW, sign_ev
from bie.qa.release_v2.contracts import ContractError,canonical_bytes
from bie.qa.release_v2.trust import TrustedKey,HmacEvidenceVerifier,TrustResult
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.release_v2.diagnostics import Diagnostic
from bie.qa.publication_v2.report_policy import TERMINAL_SCHEMA,FACT_SCHEMA,LEDGER_SCHEMA,TerminalRequirement
from bie.qa.publication_v2.terminal import BAD_STATUSES,KNOWN_COLLECTIONS
from bie.qa.publication_v2.codec import loads


class H1Case(Case):
    def terminal(self,mutate,gate='video_render'):
        old=self.f.native[gate];raw=json.loads((self.root/old.path).read_text());mutate(raw)
        new=ref(self.root,old.artifact_id,old.path,raw);self.f.native[gate]=new
        self.f.proof(lambda d:d.update(source_reports=[new.to_dict()]),gate)
        return raw
    def stage(self,mutate,stage='reaudit'):
        g=next(g for g in self.f.request.governance if g.artifact_id=='exit-'+stage)
        raw=json.loads((self.root/g.path).read_text());original=raw['source_reports'][0]
        payload=json.loads((self.root/original['path']).read_text());mutate(payload)
        new=ref(self.root,original['artifact_id'],original['path'],payload)
        raw['source_reports']=[new.to_dict()];newg=ref(self.root,g.artifact_id,g.path,raw)
        self.f.request=replace(self.f.request,governance=tuple(newg if a==g else a for a in self.f.request.governance))
    def ledger(self,payload):
        value=ref(self.root,'h1-ledger','native/ledger.json',payload)
        self.terminal(lambda d:d.update(ledgers=[value.to_dict()]))
    def check_blocked(self,code):
        result=self.blocked(code);self.assertFalse(result.product_accepted)
        return result


class TypedTerminalTests(H1Case):
    def test_typed_healthy_diagnostic_ready_not_product(self):
        r=self.f.assess();self.assertTrue(r.ready_for_signing);self.assertFalse(r.product_accepted)
    def test_default_no_registry_cannot_authorize(self):
        self.f.policy=replace(self.f.policy,terminal_requirements=());self.check_blocked('TERMINAL_POLICY_UNCONFIGURED')
    def test_report_identity_cannot_diverge(self):
        self.terminal(lambda d:d.update(report_id='other-report'));self.check_blocked('TERMINAL_REPORT_ID_MISMATCH')
    def test_unknown_schema_rejected(self):
        self.terminal(lambda d:d.update(schema_version='unknown/999'));self.check_blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_unregistered_version_rejected(self):
        self.terminal(lambda d:d.update(schema_version='bie.qa.terminal-report/2'));self.check_blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_unknown_hidden_collection_rejected(self):
        self.terminal(lambda d:d.update(hidden_checks=[{'status':'FAIL'}]));self.check_blocked('TERMINAL_FIELDS')
    def test_nested_deep_failure_propagates(self):
        child=dict(check_id='inner',status='FAIL',diagnostics=[dict(code='MISSING_FRAMES',severity='BLOCKING')],checks=[])
        self.terminal(lambda d:d['checks'][0]['checks'].append(child));self.check_blocked('MISSING_FRAMES')
    def test_pass_status_with_nested_blocker_propagates(self):
        self.terminal(lambda d:d['checks'][0]['diagnostics'].append(dict(code='CONFIRMED_BROKEN_RENDER',severity='BLOCKING')))
        self.check_blocked('CONFIRMED_BROKEN_RENDER')
    def test_explicit_typed_advisory_retained_not_blocking(self):
        self.terminal(lambda d:d['checks'][0]['diagnostics'].append(dict(code='STYLE_NOTE',severity='ADVISORY')))
        result=self.f.assess();self.assertTrue(result.ready_for_signing)
        self.assertIn('STYLE_NOTE',next(n for n in result.graph['nodes'] if n['node_id']=='artifact:native-video_render')['advisories'])
    def test_advisory_cannot_override_failed_status(self):
        self.terminal(lambda d:d['checks'][0].update(status='FAIL',diagnostics=[dict(code='STYLE_NOTE',severity='ADVISORY')]))
        self.check_blocked('SOURCE_REPORT_NOT_CLEAR')
    def test_empty_checks_cannot_pass(self):
        self.terminal(lambda d:d.update(checks=[]));self.check_blocked('EMPTY_TERMINAL_CHECKS')
    def test_removed_required_check_cannot_pass(self):
        self.terminal(lambda d:d['checks'][0].update(check_id='different'));self.check_blocked('MISSING_REQUIRED_TERMINAL_CHECK')
    def test_duplicate_check_identity_rejected(self):
        self.terminal(lambda d:d['checks'].append(d['checks'][0].copy()));self.check_blocked('DUPLICATE_TERMINAL_CHECK')
    def test_duplicate_diagnostic_rejected(self):
        self.terminal(lambda d:d['diagnostics'].extend([dict(code='NOTE',severity='ADVISORY')]*2));self.check_blocked('DUPLICATE_TERMINAL_DIAGNOSTIC')
    def test_unknown_severity_rejected(self):
        self.terminal(lambda d:d['diagnostics'].append(dict(code='X',severity='IGNORE')));self.assertFalse(self.f.assess().ready_for_signing)
    def test_string_diagnostic_cannot_hide_as_warning(self):
        self.terminal(lambda d:d['diagnostics'].append('ADVISORY:BAD'));self.check_blocked('INVALID_TYPED_DIAGNOSTIC')
    def test_nonjson_terminal_rejected_without_extension_bypass(self):
        old=self.f.native['video_render'];new=ref(self.root,old.artifact_id,'native/render.txt',b'PASS')
        self.f.proof(lambda d:d.update(source_reports=[new.to_dict()]));self.check_blocked('PUBLICATION_JSON_INVALID')
    def test_json_in_txt_still_validated(self):
        old=self.f.native['video_render'];new=ref(self.root,old.artifact_id,'native/render.txt',{'status':'PASS'})
        self.f.proof(lambda d:d.update(source_reports=[new.to_dict()]));self.check_blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_duplicate_json_keys_rejected(self):
        old=self.f.native['video_render'];new=ref(self.root,old.artifact_id,old.path,b'{"schema_version":"a","schema_version":"b"}')
        self.f.proof(lambda d:d.update(source_reports=[new.to_dict()]));self.check_blocked('DUPLICATE_JSON_KEY')
    def test_terminal_requirement_cannot_come_from_request(self):
        raw=self.f.request.to_dict();raw['terminal_requirements']=[]
        with self.assertRaises(ContractError):loads(canonical_bytes(raw))
    def test_unknown_policy_adapter_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy.terminal_requirements[0],allowed_schemas=('arbitrary/1',))
    def test_duplicate_policy_subject_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.policy,terminal_requirements=self.f.policy.terminal_requirements+(self.f.policy.terminal_requirements[0],))
    def test_subject_must_exist_in_policy(self):
        with self.assertRaises(ContractError):replace(self.f.policy,terminal_requirements=(replace(self.f.policy.terminal_requirements[0],subject_id='nonexistent'),))
    def test_production_rejects_diagnostic_terminals(self):
        self.f.policy=replace(self.f.policy,mode='production');self.check_blocked('SYNTHETIC_SOURCE_REPORT')
    def test_healthy_and_bad_inputs_remain_read_only(self):
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.f.assess();after={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)


class BindingAndTimeTests(H1Case):
    def test_terminal_creation_future(self):
        self.terminal(lambda d:d.update(created_at=NOW+1,expires_at=NOW+100));self.check_blocked('FUTURE_TERMINAL_EVIDENCE')
    def test_expired_terminal_with_fresh_wrapper(self):
        self.terminal(lambda d:d.update(expires_at=NOW));self.check_blocked('EXPIRED_TERMINAL_EVIDENCE')
    def test_terminal_created_after_wrapper(self):
        self.terminal(lambda d:d.update(created_at=NOW-1));self.check_blocked('TERMINAL_AFTER_WRAPPER')
    def test_capture_after_creation_rejected(self):
        self.terminal(lambda d:d.update(captured_at=NOW));self.check_blocked('TERMINAL_CAPTURE_AFTER_CREATION')
    def test_stale_capture_cannot_borrow_new_creation(self):
        self.terminal(lambda d:d.update(captured_at=NOW-604801));self.check_blocked('STALE_TERMINAL_CAPTURE')
    def test_overlong_terminal_lifetime_rejected(self):
        self.terminal(lambda d:d.update(expires_at=NOW+604801));self.check_blocked('TERMINAL_LIFETIME_EXCEEDED')
    def test_boolean_timestamp_rejected(self):
        self.terminal(lambda d:d.update(created_at=True));self.assertFalse(self.f.assess().ready_for_signing)
    def test_missing_time_not_timeless(self):
        self.terminal(lambda d:d.pop('captured_at'));self.check_blocked('TERMINAL_FIELDS')
    def test_scope_cannot_be_foreign(self):
        self.terminal(lambda d:d['binding'].update(subject_type='section_exit'));self.check_blocked('TERMINAL_BINDING_MISMATCH')
    def test_inspected_bytes_must_match_candidate_refs(self):
        self.terminal(lambda d:d['binding']['inspected_artifacts'][0].update(sha256='f'*64));self.check_blocked('PUBLICATION_ARTIFACT_ALIAS')
    def test_inspected_inventory_cannot_be_empty(self):
        self.terminal(lambda d:d['binding'].update(inspected_artifacts=[]));self.check_blocked('TERMINAL_INSPECTED_BINDING_MISMATCH')
    def test_duplicate_inspected_ref_rejected(self):
        self.terminal(lambda d:d['binding']['inspected_artifacts'].append(d['binding']['inspected_artifacts'][0].copy()));self.check_blocked('TERMINAL_INSPECTED_DUPLICATE')
    def test_terminal_expiry_caps_certificate(self):
        self.terminal(lambda d:d.update(expires_at=NOW+20));c=self.f.issue()
        self.assertEqual(c['expires_at'],NOW+20);self.assertEqual(c['status'],'DIAGNOSTIC_ONLY')
        self.assertFalse(c['release_authorized'])
    def test_expired_terminal_cannot_verify_old_certificate(self):
        self.terminal(lambda d:d.update(expires_at=NOW+20));c=self.f.issue()
        with self.assertRaises(ContractError):self.f.verify(c,as_of=NOW+20)
    def test_governance_bundle_binding_required(self):
        self.stage(lambda d:d['binding'].update(bundle_digest='f'*64));self.check_blocked('TERMINAL_BINDING_MISMATCH')
    def test_governance_scope_binding_required(self):
        self.stage(lambda d:d['binding'].update(subject_id='audit'));self.check_blocked('TERMINAL_BINDING_MISMATCH')
    def test_governance_run_binding_required(self):
        self.stage(lambda d:d['binding'].update(run_id='other'));self.check_blocked('TERMINAL_BINDING_MISMATCH')
    def test_governance_own_expiry_checked(self):
        self.stage(lambda d:d.update(expires_at=NOW));self.check_blocked('EXPIRED_TERMINAL_EVIDENCE')
    def test_expiry_replay_not_granted_by_refreshed_approval(self):
        self.terminal(lambda d:d.update(expires_at=NOW+2));self.assertTrue(self.f.assess().ready_for_signing)
        self.assertFalse(self.f.assess(as_of=NOW+2).ready_for_signing)
    def test_immutable_fact_checked_without_clock_fields(self):
        a=self.f.request.bundle.candidate.artifacts[0]
        self.terminal(lambda d:d['immutable_facts'].append(dict(schema_version=FACT_SCHEMA,fact_kind='artifact_identity',artifact=a.to_dict(),justification='Exact content identity only; no execution or current validity claim.')))
        self.assertTrue(self.f.assess().ready_for_signing)
    def test_immutable_fact_cannot_stand_in_for_gate_report(self):
        a=self.f.request.bundle.candidate.artifacts[0]
        self.terminal(lambda d:(d.clear(),d.update(schema_version=FACT_SCHEMA,fact_kind='artifact_identity',artifact=a.to_dict(),justification='identity')))
        self.check_blocked('TIMELESS_FACT_NOT_GATE_PROOF')
    def test_timeless_execution_fact_rejected(self):
        a=self.f.request.bundle.candidate.artifacts[0]
        self.terminal(lambda d:d['immutable_facts'].append(dict(schema_version=FACT_SCHEMA,fact_kind='successful_render',artifact=a.to_dict(),justification='not actually timeless')))
        self.check_blocked('IMMUTABLE_FACT_SCHEMA')
    def test_missing_fact_justification_rejected(self):
        a=self.f.request.bundle.candidate.artifacts[0]
        self.terminal(lambda d:d['immutable_facts'].append(dict(schema_version=FACT_SCHEMA,fact_kind='artifact_identity',artifact=a.to_dict(),justification='')))
        self.check_blocked('TERMINAL_TEXT')
    def test_fact_post_check_byte_change_blocks(self):
        a=self.f.request.bundle.candidate.artifacts[0]
        self.terminal(lambda d:d['immutable_facts'].append(dict(schema_version=FACT_SCHEMA,fact_kind='artifact_identity',artifact=a.to_dict(),justification='exact identity')))
        (self.root/a.path).write_bytes(b'changed');self.assertFalse(self.f.assess().ready_for_signing)


class LedgerTests(H1Case):
    def test_typed_empty_ledger_is_not_itself_a_gate(self):
        self.terminal(lambda d:(d.clear(),d.update(schema_version=LEDGER_SCHEMA,collections=[])))
        self.check_blocked('LEDGER_NOT_GATE_PROOF')
    def test_typed_closed_ledger_with_actual_closure_file(self):
        a=ref(self.root,'closure','native/closure.txt',b'SYNTHETIC closure evidence; not real acceptance.')
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='qa',items=[dict(obligation_id='x',status='CLOSED',closure_artifact=a.to_dict())])]))
        self.assertTrue(self.f.assess().ready_for_signing)
    def test_closed_string_without_evidence_rejected(self):
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='qa',items=[dict(obligation_id='x',status='CLOSED',closure_artifact=None)])]))
        self.check_blocked('OBLIGATION_CLOSURE_EVIDENCE_MISSING')
    def test_open_obligation_in_typed_ledger(self):
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='late-batch',items=[dict(obligation_id='x',status='OPEN',closure_artifact=None)])]))
        self.check_blocked('SOURCE_REPORT_OPEN_GAPS')
    def test_unknown_ledger_collection_field_cannot_hide(self):
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[],hidden_open=[{'status':'OPEN'}]));self.check_blocked('TERMINAL_FIELDS')
    def test_unknown_legacy_collection_rejected(self):
        self.ledger(dict(schema_version='1.0.0',scope='test',gaps=[],batch999_open_obligations=[{'id':'x','status':'OPEN'}]));self.check_blocked('TERMINAL_FIELDS')
    def test_duplicate_obligation_rejected(self):
        row=dict(obligation_id='x',status='OPEN',closure_artifact=None)
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='a',items=[row,row])]));self.check_blocked('DUPLICATE_OBLIGATION_ID')
    def test_duplicate_collection_rejected(self):
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='a',items=[])]*2));self.check_blocked('DUPLICATE_OBLIGATION_COLLECTION')
    def test_actual_cumulative_ledger_all_113_obligations_preserved(self):
        raw=json.loads((Path(__file__).resolve().parents[2]/'history/section16_pre_h1/QA_SECTION16_GAP_LEDGER.json').read_text())
        self.ledger(raw);self.check_blocked('SOURCE_REPORT_OPEN_GAPS')
    def test_legacy_closed_ledger_cannot_omit_bindings(self):
        self.ledger(dict(schema_version='1.0.0',scope='legacy',gaps=[]));self.check_blocked('LEGACY_LEDGER_NOT_BOUND_TERMINAL')
    def test_closure_artifact_tampering_rejected(self):
        a=ref(self.root,'closure','native/closure.txt',b'SYNTHETIC closure')
        self.ledger(dict(schema_version=LEDGER_SCHEMA,collections=[dict(collection_id='q',items=[dict(obligation_id='x',status='CLOSED',closure_artifact=a.to_dict())])]))
        (self.root/a.path).write_bytes(b'changed');self.assertFalse(self.f.assess().ready_for_signing)
    def test_dependency_self_cycle_rejected(self):
        a=self.f.native['video_render'];self.terminal(lambda d:d['ledgers'].append(a.to_dict()));self.check_blocked('TERMINAL_DEPENDENCY_CYCLE')


# Distinct required boundary cases, not synthetic rerun/subcase count inflation.
for status in BAD_STATUSES:
    def make_status(value):
        def test(self):
            self.terminal(lambda d:d['checks'][0]['checks'].append(dict(check_id='nested',status=value,diagnostics=[],checks=[])))
            self.check_blocked('SOURCE_REPORT_NOT_CLEAR')
        return test
    setattr(TypedTerminalTests,'test_nested_status_'+status,make_status(status))
for field,value in [('candidate_digest','e'*64),('run_id','foreign'),('revision','e'*40),('subject_id','another_gate'),('evidence_id','other-evidence'),('release_policy_digest','e'*64),('evaluator_policy_digest','e'*64),('bundle_digest','e'*64)]:
    def make_binding(field,value):
        def test(self):
            self.terminal(lambda d:d['binding'].update({field:value}));self.check_blocked('TERMINAL_BINDING_MISMATCH')
        return test
    setattr(BindingAndTimeTests,'test_foreign_'+field,make_binding(field,value))
for collection in KNOWN_COLLECTIONS:
    def make_collection(collection):
        def test(self):
            raw=dict(schema_version='1.0.0',scope='SYNTHETIC',gaps=[]);raw[collection]=[dict(gap_id='x',status='OPEN')]
            self.ledger(raw);self.check_blocked('SOURCE_REPORT_OPEN_GAPS')
        return test
    setattr(LedgerTests,'test_legacy_open_'+collection,make_collection(collection))


class IdentityTests(H1Case):
    def quorum(self,key1,key2):
        rp=self.f.policy.release_policy
        rp=replace(rp,gates=tuple(replace(g,min_distinct_evaluators=2) if g.gate_id=='video_render' else g for g in rp.gates))
        evs=tuple(sign_ev(replace(e,policy_digest=rp.content_digest,evaluator_id=key1.evaluator_id,signer_key_id=key1.key_id),key1) for e in self.f.request.bundle.evidence)
        base=next(e for e in evs if e.gate_id=='video_render');a=ref(self.root,'other-report','proofs/other.json',{'SYNTHETIC':'second distinct report'})
        extra=sign_ev(replace(base,evidence_id='second',report=a,evaluator_id=key2.evaluator_id,signer_key_id=key2.key_id),key2)
        bundle=replace(self.f.request.bundle,evidence=evs+(extra,))
        return ReleaseEvaluator(rp,HmacEvidenceVerifier((key1,key2))).evaluate(bundle,self.root,as_of=NOW)
    def keys(self):
        a=replace(self.f.evkey,principal_id='reviewer-a',independence_group='org-a')
        b=replace(a,key_id='second-key',evaluator_id='second-evaluator',secret=b'SYNTHETIC-OTHER-SECRET-0000000000000',principal_id='reviewer-b',independence_group='org-b')
        return a,b
    def test_distinct_valid_independent_principals_satisfy_floor(self):
        r=self.quorum(*self.keys());self.assertTrue(r.ready_for_review);self.assertFalse(r.release_authorized)
    def test_shared_secret_explicit_independent_names_rejected(self):
        a,b=self.keys()
        with self.assertRaisesRegex(ContractError,'SHARED_SECRET_IDENTITY_CONFLICT'):HmacEvidenceVerifier((a,replace(b,secret=a.secret)))
    def test_shared_principal_different_keys_not_independent(self):
        a,b=self.keys();r=self.quorum(a,replace(b,principal_id=a.principal_id,independence_group=a.independence_group));self.assertFalse(r.ready_for_review)
    def test_shared_group_distinct_principals_not_independent(self):
        a,b=self.keys();r=self.quorum(a,replace(b,independence_group=a.independence_group));self.assertFalse(r.ready_for_review)
    def test_legacy_aliases_sharing_secret_do_not_satisfy_floor(self):
        a=self.f.evkey;b=replace(a,key_id='alias-key',evaluator_id='alias-name');self.assertFalse(self.quorum(a,b).ready_for_review)
    def test_unmapped_legacy_different_secrets_do_not_infer_independence(self):
        a=self.f.evkey;b=replace(a,key_id='alias-key',evaluator_id='alias-name',secret=b'NEW-SYNTHETIC-SECRET-00000000000000');self.assertFalse(self.quorum(a,b).ready_for_review)
    def test_principal_cannot_change_group_between_keys(self):
        a,b=self.keys()
        with self.assertRaisesRegex(ContractError,'PRINCIPAL_GROUP_CONFLICT'):HmacEvidenceVerifier((a,replace(b,principal_id=a.principal_id)))
    def test_key_revoked_at_current_clock_rejected(self):
        self.assertEqual(HmacEvidenceVerifier((replace(self.f.evkey,revoked_at=NOW),)).verify_at(self.f.ev(),as_of=NOW).diagnostic,'REVOKED_SIGNER')
    def test_key_expired_at_boundary_rejected(self):
        self.assertEqual(HmacEvidenceVerifier((replace(self.f.evkey,not_after=NOW),)).verify_at(self.f.ev(),as_of=NOW).diagnostic,'SIGNER_NOT_CURRENT')
    def test_key_not_yet_valid_rejected(self):
        self.assertEqual(HmacEvidenceVerifier((replace(self.f.evkey,not_before=NOW+1),)).verify_at(self.f.ev(),as_of=NOW).diagnostic,'SIGNER_NOT_CURRENT')
    def test_record_created_before_key_start_rejected(self):
        self.assertEqual(HmacEvidenceVerifier((replace(self.f.evkey,not_before=NOW-1),)).verify_at(self.f.ev(),as_of=NOW).diagnostic,'EVIDENCE_OUTSIDE_KEY_LIFETIME')
    def test_record_cannot_exceed_key_lifetime(self):
        self.assertEqual(HmacEvidenceVerifier((replace(self.f.evkey,not_after=NOW+10),)).verify_at(self.f.ev(),as_of=NOW).diagnostic,'EVIDENCE_EXCEEDS_KEY_LIFETIME')
    def test_future_revocation_caps_certificate(self):
        self.f.verifier=HmacEvidenceVerifier((replace(self.f.evkey,revoked_at=NOW+10),));c=self.f.issue();self.assertEqual(c['expires_at'],NOW+10)
    def test_disabled_old_rotated_key_does_not_borrow_new_key(self):
        a,b=self.keys();v=HmacEvidenceVerifier((replace(a,enabled=False),replace(b,principal_id=a.principal_id,independence_group=a.independence_group)))
        ev=sign_ev(replace(self.f.ev(),evaluator_id=a.evaluator_id,signer_key_id=a.key_id),a)
        self.assertFalse(v.verify_at(ev,as_of=NOW).accepted)
    def test_revocation_blocks_formerly_ready_evaluation(self):
        self.f.verifier=HmacEvidenceVerifier((replace(self.f.evkey,revoked_at=NOW+1),))
        self.assertTrue(self.f.assess().ready_for_signing);self.assertFalse(self.f.assess(as_of=NOW+1).ready_for_signing)
    def test_partial_identity_configuration_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.evkey,principal_id='x')
    def test_boolean_key_clock_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.evkey,not_before=True)
    def test_empty_key_lifetime_rejected(self):
        with self.assertRaises(ContractError):replace(self.f.evkey,not_before=NOW,not_after=NOW)
    def test_clockless_plugin_cannot_authorize(self):
        class Old:
            def verify(self,e):return TrustResult(True,'OK','operator_managed')
        self.assertFalse(self.f.assess(verifier=Old()).ready_for_signing)
    def test_plugin_missing_identity_fails_closed(self):
        class Incomplete:
            def verify_at(self,e,*,as_of):return TrustResult(True,'OK','operator_managed')
        result=self.f.assess(verifier=Incomplete());self.assertFalse(result.ready_for_signing)
        self.assertIn('UNVERIFIED_PRINCIPAL_IDENTITY',{b['code'] for b in result.blockers})
    def test_secret_not_in_report(self):
        self.assertNotIn(self.f.evkey.secret,self.f.assess().to_bytes())


class DiagnosticMonotonicityTests(H1Case):
    def test_lower_and_publication_both_retain_blocker(self):
        self.f.update_ev(diagnostics=('CONFIRMED_BROKEN_RENDER',))
        result=ReleaseEvaluator(self.f.policy.release_policy,self.f.verifier).evaluate(self.f.request.bundle,self.root,as_of=NOW)
        self.assertFalse(result.ready_for_review)
        self.assertIn('CONFIRMED_BROKEN_RENDER',{c for g in result.gate_results for e in g.evidence for c in e.diagnostics})
        self.check_blocked('CONFIRMED_BROKEN_RENDER')
    def test_legacy_advisory_string_is_not_downgrade(self):
        self.f.update_ev(diagnostics=('ADVISORY:CONFIRMED_BROKEN_RENDER',));self.assertFalse(self.f.assess().ready_for_signing)
    def test_pass_score_cannot_overrule_diagnostic(self):
        self.f.update_ev(diagnostics=('CRITICAL_DEFECT',));self.assertFalse(self.f.assess().ready_for_signing)
    def legacy(self,gate_id=None,mode=None):
        from bie.qa import release_contracts as legacy
        p=legacy.enterprise_default_policy(False,False)
        if mode is not None:p=replace(p,gates=[replace(g,mode=mode) if g.gate_id=='performance' else g for g in p.gates])
        es=[legacy.GateEvidence('e-'+g.gate_id,g.gate_id,'PASS','test','1',['source'],['report']) for g in p.gates if g.mode=='REQUIRED']
        if gate_id is not None:es.append(legacy.GateEvidence('bad',gate_id,'PASS','test','1',['source'],['report'],diagnostics=['CONFIRMED_BROKEN_RENDER']))
        return legacy.ReleaseEvaluator.evaluate(p,es)
    def test_legacy_metadata_cannot_return_success(self):
        r=self.legacy();self.assertEqual(r.release_status,'CONTRACT_ONLY');self.assertFalse(r.release_authorized)
    def test_legacy_required_diagnostic_blocks(self):
        r=self.legacy('source_grounding');self.assertEqual(r.release_status,'BLOCKED')
    def test_legacy_optional_diagnostic_blocks(self):
        r=self.legacy('performance');self.assertEqual(r.release_status,'BLOCKED')
    def test_legacy_not_applicable_cannot_drop_diagnostic(self):
        r=self.legacy('performance','NOT_APPLICABLE');self.assertEqual(r.release_status,'BLOCKED')
        self.assertIn('CONFIRMED_BROKEN_RENDER',next(g for g in r.gate_results if g.gate_id=='performance').diagnostics)
    def test_legacy_unknown_gate_keeps_diagnostic(self):
        r=self.legacy('newgate');self.assertEqual(r.release_status,'BLOCKED')
        self.assertIn('CONFIRMED_BROKEN_RENDER',next(g for g in r.gate_results if g.gate_id=='newgate').diagnostics)
    def test_no_diagnostic_normalization_discards_code(self):
        d=Diagnostic('SCORE_100_BUT_FAILED');self.assertEqual(d.severity,'BLOCKING')

if __name__=='__main__':unittest.main()
