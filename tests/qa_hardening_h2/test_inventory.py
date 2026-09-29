from h2_support import *
from bie.qa.publication_v2.codec import loads
from bie.qa.governance_v2.catalog import ORIGINAL_TASK_IDS,HARDENING_TASK_IDS,BASELINE_OBLIGATIONS,CATALOG_DIGEST

class Census(InventoryCase):
    def test_valid_diagnostic_not_product(self):
        x=self.f.assess();self.assertTrue(x.ready_for_signing);self.assertFalse(x.product_accepted)
    def test_no_authority_denied(self):
        self.f.policy=replace(self.f.policy,inventory_authority=None);self.blocked('AUTHORITATIVE_INVENTORY_UNCONFIGURED')
    def test_no_inventory_denied(self):
        self.f.request=replace(self.f.request,inventory=None);self.blocked('AUTHORITATIVE_INVENTORY_MISSING')
    def test_old_request_readable_not_ready(self):
        d=self.f.request.to_dict();d.pop('inventory');self.f.request=loads(canonical_bytes(d));self.blocked('AUTHORITATIVE_INVENTORY_MISSING')
    def test_authority_not_request_field(self):
        d=self.f.request.to_dict();d['inventory_authority']={}
        with self.assertRaises(ContractError):loads(canonical_bytes(d))
    def test_nested_key_not_request_field(self):self.mutate(lambda d:d.update(closure_keys=[]));self.blocked('PUBLICATION_FIELDS')
    def test_unknown_schema(self):self.mutate(lambda d:d.update(schema_version='unknown/1'));self.blocked('INVENTORY_SCHEMA')
    def test_authority_digest_mismatch(self):self.mutate(lambda d:d.update(authority_digest='f'*64));self.blocked('INVENTORY_BINDING_MISMATCH')
    def test_foreign_run(self):self.mutate(lambda d:d.update(run_id='different'));self.blocked('INVENTORY_BINDING_MISMATCH')
    def test_foreign_candidate(self):self.mutate(lambda d:d.update(candidate_digest='f'*64));self.blocked('INVENTORY_BINDING_MISMATCH')
    def test_foreign_revision(self):self.mutate(lambda d:d.update(revision='f'*40));self.blocked('INVENTORY_BINDING_MISMATCH')
    def test_future_inventory(self):self.mutate(lambda d:d.update(created_at=NOW+1));self.blocked('INVENTORY_TIME')
    def test_expired_inventory(self):self.mutate(lambda d:d.update(expires_at=NOW));self.blocked('INVENTORY_TIME')
    def test_long_lived_inventory(self):self.mutate(lambda d:d.update(expires_at=NOW+700000));self.blocked('INVENTORY_LIFETIME')
    def test_missing_artifact(self):self.mutate(lambda d:d['artifacts'].pop());self.blocked('INVENTORY_ARTIFACT_CENSUS')
    def test_empty_artifacts(self):self.mutate(lambda d:d.update(artifacts=[]));self.blocked('INVENTORY_ARTIFACT_CENSUS')
    def test_duplicate_artifact(self):self.mutate(lambda d:d['artifacts'].append(d['artifacts'][0]));self.blocked('INVENTORY_DUPLICATE_ARTIFACT')
    def test_changed_role(self):self.mutate(lambda d:d['artifacts'][0].update(role='support'));self.blocked('INVENTORY_ARTIFACT_CENSUS')
    def test_candidate_omission_not_smaller_scope(self):
        a=self.f.policy.inventory_authority
        additional=ref(self.root,'second-source','subjects/second.txt',b'Another required source','source')
        self.f.policy=replace(self.f.policy,inventory_authority=replace(a,artifacts=a.artifacts+(additional,)))
        self.blocked('AUTHORITATIVE_ARTIFACT_MISMATCH')
    def test_actual_bytes_checked(self):
        p=self.root/self.f.policy.inventory_authority.artifacts[0].path;p.write_bytes(b'changed')
        self.assertFalse(self.f.assess().ready_for_signing)
    def test_missing_task(self):self.mutate(lambda d:d.update(task_ids=[]));self.blocked('INVENTORY_TASK_CENSUS')
    def test_extra_task(self):self.mutate(lambda d:d['task_ids'].append('phantom'));self.blocked('INVENTORY_TASK_CENSUS')
    def test_duplicate_task(self):self.mutate(lambda d:d['task_ids'].append(d['task_ids'][0]));self.blocked('INVENTORY_DUPLICATE')
    def test_missing_subject(self):self.mutate(lambda d:d['checks'].pop());self.blocked('INVENTORY_CHECK_CENSUS')
    def test_missing_check(self):self.mutate(lambda d:d['checks'][0].update(check_ids=[]));self.blocked('INVENTORY_CHECK_CENSUS')
    def test_duplicate_subject(self):self.mutate(lambda d:d['checks'].append(d['checks'][0]));self.blocked('INVENTORY_DUPLICATE_CHECK_SUBJECT')
    def test_removed_policy_requirement(self):
        self.f.policy=replace(self.f.policy,terminal_requirements=self.f.policy.terminal_requirements[:-1]);self.blocked('AUTHORITATIVE_CHECK_POLICY_MISMATCH')
    def test_outer_check_removed(self):self.f.proof(lambda d:d.update(checks=[]));self.blocked('MISSING_AUTHORITATIVE_PROOF_CHECK')
    def test_open_gap_preserved(self):self.need_gap();self.blocked('AUTHORITATIVE_OBLIGATION_OPEN')
    def test_missing_gap_not_smaller_denominator(self):self.need_gap();self.mutate(lambda d:d.update(obligations=[]));self.blocked('INVENTORY_OBLIGATION_CENSUS')
    def test_duplicate_gap(self):self.need_gap();self.mutate(lambda d:d['obligations'].append(d['obligations'][0]));self.blocked('INVENTORY_DUPLICATE_OBLIGATION')
    def test_plain_closed_string_not_evidence(self):self.need_gap();self.mutate(lambda d:d['obligations'][0].update(status='CLOSED'));self.blocked('OBLIGATION_CLOSURE_MISSING')
    def test_changed_gap_owner(self):self.need_gap();self.mutate(lambda d:d['obligations'][0].update(owner='elsewhere'));self.blocked('OBLIGATION_DEFINITION_MISMATCH')
    def test_changed_gap_scope(self):self.need_gap();self.mutate(lambda d:d['obligations'][0].update(scope='NOT_REQUIRED'));self.blocked('OBLIGATION_DEFINITION_MISMATCH')
    def test_changed_gap_definition(self):self.need_gap();self.mutate(lambda d:d['obligations'][0].update(definition_digest='a'*64));self.blocked('OBLIGATION_DEFINITION_MISMATCH')
    def test_unknown_status_not_deferral(self):self.need_gap();self.mutate(lambda d:d['obligations'][0].update(status='WAIVED'));self.blocked('OBLIGATION_STATUS')
    def test_diagnostic_inventory_never_production(self):self.f.policy=replace(self.f.policy,mode='production');self.blocked('DIAGNOSTIC_INVENTORY_NOT_PRODUCTION')
    def test_production_cannot_shrink_original_tasks(self):
        with self.assertRaisesRegex(ContractError,'SECTION16_TASK_BASELINE_MISSING'):replace(self.f.policy.inventory_authority,profile='SECTION16')
    def test_section_catalog_counts(self):
        self.assertEqual(len(ORIGINAL_TASK_IDS),76);self.assertEqual(len(HARDENING_TASK_IDS),41);self.assertEqual(len(BASELINE_OBLIGATIONS),113)
    def test_production_cannot_omit_obligations(self):
        with self.assertRaisesRegex(ContractError,'SECTION16_OBLIGATION_BASELINE_MISSING'):
            replace(self.f.policy.inventory_authority,profile='SECTION16',task_ids=ORIGINAL_TASK_IDS+HARDENING_TASK_IDS)
    def test_read_only(self):
        before={str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()};self.f.assess()
        self.assertEqual(before,{str(p):p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_identity_order_not_scope(self):
        self.mutate(lambda d:(d['artifacts'].reverse(),d['checks'].reverse()));self.assertTrue(self.f.assess().ready_for_signing)
    def test_inventory_caps_certificate_expiry(self):
        self.mutate(lambda d:d.update(expires_at=NOW+10));self.assertEqual(self.f.issue()['expires_at'],NOW+10)
    def test_inventory_alias_to_proof_rejected(self):
        self.f.request=replace(self.f.request,inventory=self.f.ev().report);self.blocked('INVENTORY_REPORT_ALIAS')

class Closures(GapCase):
    def test_valid_closure(self):self.assertTrue(self.f.assess().ready_for_signing)
    def test_no_approvals(self):self.mutate_closure(lambda d:d.update(approvals=[]),False);self.blocked('CLOSURE_INDEPENDENCE_FLOOR')
    def test_bad_signature(self):self.mutate_closure(lambda d:d['approvals'][0].update(signature='a'*64),False);self.blocked('BAD_CLOSURE_SIGNATURE')
    def test_wrong_principal(self):self.mutate_closure(lambda d:d['approvals'][0].update(principal_id='fake'),False);self.blocked('UNAUTHORIZED_CLOSURE_PRINCIPAL')
    def test_wrong_purpose(self):self.mutate_closure(lambda d:d['approvals'][0].update(purpose='inventory'),False);self.blocked('UNAUTHORIZED_CLOSURE_PRINCIPAL')
    def test_unknown_key(self):self.mutate_closure(lambda d:d['approvals'][0].update(key_id='unknown'),False);self.blocked('UNKNOWN_CLOSURE_KEY')
    def test_closure_foreign_revision(self):self.mutate_closure(lambda d:d.update(revision='a'*40));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_foreign_run(self):self.mutate_closure(lambda d:d.update(run_id='other'));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_foreign_candidate(self):self.mutate_closure(lambda d:d.update(candidate_digest='a'*64));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_foreign_catalog(self):self.mutate_closure(lambda d:d.update(authority_digest='a'*64));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_wrong_scope(self):self.mutate_closure(lambda d:d.update(scope='PRODUCT'));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_wrong_obligation(self):self.mutate_closure(lambda d:d.update(obligation_id='other'));self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_closure_future(self):self.mutate_closure(lambda d:d.update(created_at=NOW+1));self.blocked('CLOSURE_TIME')
    def test_closure_expired(self):self.mutate_closure(lambda d:d.update(expires_at=NOW));self.blocked('CLOSURE_TIME')
    def test_closure_lifetime(self):self.mutate_closure(lambda d:d.update(expires_at=NOW+700000));self.blocked('CLOSURE_LIFETIME')
    def test_no_closure_reports(self):self.mutate_closure(lambda d:d.update(evidence=[]));self.blocked('CLOSURE_EVIDENCE_MISSING')
    def test_duplicate_closure_reports(self):self.mutate_closure(lambda d:d['evidence'].append(d['evidence'][0]));self.blocked('CLOSURE_EVIDENCE_ALIAS')
    def test_unknown_closure_schema(self):self.mutate_closure(lambda d:d.update(schema_version='closure/999'));self.blocked('CLOSURE_SCHEMA')
    def test_report_missing_check(self):self.mutate_evidence(lambda d:d.update(checks=[]));self.blocked('MISSING_REQUIRED_TERMINAL_CHECK')
    def test_report_failed_check(self):self.mutate_evidence(lambda d:d['checks'][0].update(status='FAIL'));self.blocked('SOURCE_REPORT_NOT_CLEAR')
    def test_report_foreign_revision(self):self.mutate_evidence(lambda d:d['binding'].update(revision='a'*40));self.blocked('TERMINAL_BINDING_MISMATCH')
    def test_report_foreign_scope(self):self.mutate_evidence(lambda d:d.update(scope='NATIVE_PRODUCT'));self.blocked('CLOSURE_EVIDENCE_SCOPE_MISMATCH')
    def test_report_omitted_artifact(self):self.mutate_evidence(lambda d:d['binding'].update(inspected_artifacts=[]));self.blocked('TERMINAL_INSPECTED_BINDING_MISMATCH')
    def test_report_unknown_schema(self):self.mutate_evidence(lambda d:d.update(schema_version='madeup/1'));self.blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_report_future(self):self.mutate_evidence(lambda d:d.update(created_at=NOW+1));self.blocked('FUTURE_TERMINAL_EVIDENCE')
    def test_report_expired(self):self.mutate_evidence(lambda d:d.update(expires_at=NOW));self.blocked('EXPIRED_TERMINAL_EVIDENCE')
    def test_report_tampered_bytes(self):
        (self.root/'closure/evidence.json').write_bytes(b'changed');self.assertFalse(self.f.assess().ready_for_signing)
    def test_report_caps_certificate_expiry(self):
        self.mutate_evidence(lambda d:d.update(expires_at=NOW+12));self.assertEqual(self.f.issue()['expires_at'],NOW+12)
    def test_key_revocation_invalidates_prior_closure(self):
        a=self.f.policy.inventory_authority;self.f.policy=replace(self.f.policy,inventory_authority=replace(a,closure_keys=(replace(self.k,enabled=False),)))
        self.blocked('REVOKED_CLOSURE_KEY')
    def test_key_expired(self):
        a=self.f.policy.inventory_authority;self.f.policy=replace(self.f.policy,inventory_authority=replace(a,closure_keys=(replace(self.k,not_after=NOW),)))
        self.blocked('CLOSURE_KEY_TIME')
    def test_missing_key(self):
        a=self.f.policy.inventory_authority;self.f.policy=replace(self.f.policy,inventory_authority=replace(a,closure_keys=()))
        self.blocked('UNKNOWN_CLOSURE_KEY')
    def test_quorum_not_met(self):
        a=self.f.policy.inventory_authority;self.f.policy=replace(self.f.policy,inventory_authority=replace(a,minimum_independent_closers=2))
        self.blocked('CLOSURE_INDEPENDENCE_FLOOR')
    def test_duplicate_approval(self):self.mutate_closure(lambda d:d['approvals'].append(d['approvals'][0]),False);self.blocked('DUPLICATE_CLOSURE_APPROVAL')
    def test_shared_secret_identity_rejected(self):
        a=self.f.policy.inventory_authority
        with self.assertRaises(ContractError):replace(a,closure_keys=(self.k,replace(self.k,key_id='second',principal_id='second',independence_group='second')))
    def test_authority_definition_change_invalidates_closure(self):
        a=self.f.policy.inventory_authority
        self.f.policy=replace(self.f.policy,inventory_authority=replace(a,obligations=(replace(self.o,definition_digest='f'*64),)))
        self.blocked('CLOSURE_BINDING_MISMATCH')
    def test_expired_inventory_cannot_borrow_good_closure(self):self.mutate(lambda d:d.update(expires_at=NOW));self.blocked('INVENTORY_TIME')
