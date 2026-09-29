from pub22_support import *
from dataclasses import replace
class Proofs(Case):
    def test_unsigned_is_blocked(self):
        a=self.f.assess(verifier=None);self.assertFalse(a.ready_for_signing)
    def test_signature_changed(self):self.f.update_ev(signature='0'*64,resign=False);self.blocked('BAD_SIGNATURE')
    def test_revoked_gate_key(self):
        v=HmacEvidenceVerifier((replace(self.f.evkey,enabled=False),));a=self.f.assess(verifier=v);self.assertFalse(a.ready_for_signing)
    def test_test_only_evidence_no_pass(self):
        a=self.f.assess(verifier=HmacEvidenceVerifier((replace(self.f.evkey,assurance='test_only'),)));self.assertFalse(a.ready_for_signing)
    def test_gate_candidate_mismatch(self):self.f.update_ev(candidate_digest='a'*64);self.blocked('CANDIDATE_BINDING_MISMATCH')
    def test_gate_revision_mismatch(self):self.f.update_ev(revision='a'*40);self.blocked('REVISION_BINDING_MISMATCH')
    def test_gate_run_mismatch(self):self.f.update_ev(run_id='another');self.blocked('RUN_BINDING_MISMATCH')
    def test_gate_policy_mismatch(self):self.f.update_ev(policy_digest='a'*64);self.blocked('POLICY_BINDING_MISMATCH')
    def test_expired(self):self.f.update_ev(created_at=NOW-20,expires_at=NOW);self.blocked('EXPIRED_EVIDENCE')
    def test_future(self):self.f.update_ev(created_at=NOW+1,expires_at=NOW+30);self.blocked('FUTURE_EVIDENCE')
    def test_unknown_gate(self):
        ev=sign_ev(replace(self.f.ev(),evidence_id='extra',gate_id='unknown'),self.f.evkey)
        self.f.request=replace(self.f.request,bundle=replace(self.f.request.bundle,evidence=self.f.request.bundle.evidence+(ev,)));self.f.refresh_governance();self.blocked('UNKNOWN_EVIDENCE_GATE')
    def test_conflicting_evidence_not_outvoted(self):
        ev=sign_ev(replace(self.f.ev(),evidence_id='contrary',status='FAIL',diagnostics=('FAILED',)),self.f.evkey)
        self.f.request=replace(self.f.request,bundle=replace(self.f.request.bundle,evidence=self.f.request.bundle.evidence+(ev,)));self.f.refresh_governance();self.blocked('EVIDENCE_FAIL')
    def test_proof_status_mismatch(self):self.f.proof(lambda d:d.update(status='NOT_RUN'));self.blocked('PROOF_BINDING_MISMATCH')
    def test_empty_checks(self):self.f.proof(lambda d:d.update(checks=[]));self.blocked('EMPTY_PROOF_CHECKS')
    def test_check_failure(self):self.f.proof(lambda d:d['checks'][0].update(status='FAIL'));self.blocked('PROOF_CHECK_NOT_CLEAR')
    def test_check_skipped(self):self.f.proof(lambda d:d['checks'][0].update(status='SKIPPED'));self.blocked('PROOF_CHECK_NOT_CLEAR')
    def test_check_review(self):self.f.proof(lambda d:d['checks'][0].update(status='REVIEW_REQUIRED'));self.blocked('PROOF_CHECK_NOT_CLEAR')
    def test_check_pending_diagnostic(self):self.f.proof(lambda d:d['checks'][0].update(diagnostics=['PENDING']));self.blocked('PROOF_CHECK_NOT_CLEAR')
    def test_duplicate_checks(self):self.f.proof(lambda d:d['checks'].append(d['checks'][0].copy()));self.blocked('DUPLICATE_PROOF_CHECK')
    def test_empty_raw_reports(self):self.f.proof(lambda d:d.update(source_reports=[]));self.blocked('MISSING_SOURCE_REPORTS')
    def test_source_report_self_reference(self):
        raw=self.f.ev().report.to_dict();self.f.proof(lambda d:d.update(source_reports=[raw]));self.blocked('SOURCE_REPORT_NOT_TERMINAL')
    def test_source_report_alias(self):
        raw=self.f.native['video_render'].to_dict();raw['artifact_id']='source';self.f.proof(lambda d:d.update(source_reports=[raw]));self.blocked('SOURCE_REPORT_NOT_TERMINAL')
    def test_proof_missing_field(self):self.f.proof(lambda d:d.pop('checks'));self.blocked('PUBLICATION_FIELDS')
    def test_nonproof_legacy_report_not_promoted(self):
        e=self.f.ev();report=ref(self.root,e.report.artifact_id,e.report.path,{'status':'PASS','bounded':True});self.f.update_ev(report=report);self.blocked('PUBLICATION_FIELDS')
    def test_evidence_pending_diagnostics(self):self.f.update_ev(diagnostics=('FULL_NATIVE_PENDING',));self.blocked('UNCLEARED_EVIDENCE_DIAGNOSTICS')
    def test_governance_missing(self):self.f.request=replace(self.f.request,governance=());self.blocked('MISSING_SECTION_EXIT_EVIDENCE')
    def test_governance_missing_reaudit(self):self.f.request=replace(self.f.request,governance=self.f.request.governance[:-1]);self.blocked('MISSING_SECTION_EXIT_EVIDENCE')
    def test_governance_open_musthave(self):
        a=self.f.request.governance[0];d=json.loads((self.root/a.path).read_text());d['open_must_have_ids']=['gap'];new=ref(self.root,a.artifact_id,a.path,d)
        self.f.request=replace(self.f.request,governance=(new,)+self.f.request.governance[1:]);self.blocked('SECTION_EXIT_NOT_CLEAR')
    def test_governance_wrong_bundle(self):
        a=self.f.request.governance[0];d=json.loads((self.root/a.path).read_text());d['bundle_digest']='f'*64;new=ref(self.root,a.artifact_id,a.path,d)
        self.f.request=replace(self.f.request,governance=(new,)+self.f.request.governance[1:]);self.blocked('SECTION_EXIT_BINDING')
    def test_governance_duplicate_stage(self):
        a=self.f.request.governance[0];d=json.loads((self.root/a.path).read_text());d['stage']='hardening';new=ref(self.root,a.artifact_id,a.path,d)
        self.f.request=replace(self.f.request,governance=(new,)+self.f.request.governance[1:]);self.blocked('SECTION_EXIT_STAGE')

# Every mandatory gate is independently removed, so an accidental catalog omission
# is detected. These are 28 distinct cases, not extra counts for repeated runs.
def missing_gate(gid):
    def test(self):
        self.f.request=replace(self.f.request,bundle=replace(self.f.request.bundle,evidence=tuple(e for e in self.f.request.bundle.evidence if e.gate_id!=gid)))
        self.f.refresh_governance();a=self.blocked('MISSING_REQUIRED_EVIDENCE');self.assertIn(gid,a.inherited_gate_report['blocking_gates'])
    return test
for _g in enterprise_policy().gates:setattr(Proofs,'test_required_gate_'+_g.gate_id,missing_gate(_g.gate_id))
