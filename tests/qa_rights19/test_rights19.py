from pathlib import Path
from dataclasses import replace,asdict
import tempfile,unittest,json,hashlib,hmac,os,subprocess,sys
from rights19_support import *
from bie.qa.rights_v2.expressions import parse,single_atom,selected_branch
from bie.qa.release_v2.contracts import ContractError,ReleaseCandidate
from bie.qa.rights_v2.bridge import prepare_release_evidence
from bie.qa.repair_v2.codec import decode
from bie.qa.source_v2.codec import loads

class RightsTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshot';self.r,self.p=make_fixture(self.root)
    def check(self,code,r=None,p=None,**kw):
        result=run(r or self.r,self.root,p or self.p,**kw);self.assertIn(code,codes(result));self.assertNotEqual(result.status,'CHECKS_PASSED');return result
    def grant(self,**changes):return replace(self.p,grants=(self.p.grants[0],replace(self.p.grants[1],**changes)))
    def test_signed_bounded_checks(self):
        result=run(self.r,self.root,self.p);self.assertEqual(result.status,'CHECKS_PASSED');self.assertFalse(result.to_dict()['legal_clearance_certified'])
    def test_default_unsigned_review(self):self.assertEqual(run(self.r,self.root,self.p,signed=False).status,'REVIEW_REQUIRED')
    def test_report_deterministic(self):self.assertEqual(run(self.r,self.root,self.p).to_dict(),run(self.r,self.root,self.p).to_dict())
    def test_source_asset_reports(self):self.assertEqual([r.task_id for r in run(self.r,self.root,self.p).reports],['BIE-QA-RIGHTS-001','BIE-QA-RIGHTS-002'])
    def test_all_bytes_inspected(self):self.assertEqual(set(run(self.r,self.root,self.p).reports[0].inspected_artifact_ids),{a.artifact_id for a in self.r.snapshot.artifacts})
    def test_missing_use(self):self.check('RIGHTS_USE_INVENTORY_MISMATCH',r=replace(self.r,selections=self.r.selections[:1]))
    def test_extra_use(self):self.check('RIGHTS_USE_INVENTORY_MISMATCH',r=replace(self.r,selections=self.r.selections+(UseSelection('surplus',()),)))
    def test_no_grants(self):self.check('RIGHTS_GRANT_REQUIRED',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],grant_ids=(),notices=()))))
    def test_unknown_grant(self):self.check('RIGHTS_UNKNOWN_GRANT',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],grant_ids=('no-grant',)))))
    def test_other_material_grant(self):self.check('RIGHTS_WRONG_MATERIAL_GRANT',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],grant_ids=('source-grant',)))))
    def test_missing_obligation(self):self.check('RIGHTS_OBLIGATION_COVERAGE',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=()))))
    def test_unknown_obligation(self):
        n=replace(self.r.selections[1].notices[0],obligation_id='unknown');self.check('RIGHTS_OBLIGATION_COVERAGE',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=(n,)))))
    def test_notice_wrong_file(self):
        n=replace(self.r.selections[1].notices[0],artifact_id='terms-asset');self.check('RIGHTS_NOTICE_LOCATION',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=(n,)))))
    def test_notice_wrong_offset(self):
        n=self.r.selections[1].notices[0];n=replace(n,start=n.start+1,end=n.end+1);self.check('RIGHTS_NOTICE_TEXT_MISMATCH',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=(n,)))))
    def test_notice_past_end(self):
        n=replace(self.r.selections[1].notices[0],end=9999);self.check('RIGHTS_NOTICE_TEXT_MISMATCH',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=(n,)))))
    def test_utf8_not_character_offsets(self):
        n=self.r.selections[1].notices[0];n=replace(n,end=n.end-2);self.check('RIGHTS_NOTICE_TEXT_MISMATCH',r=replace(self.r,selections=(self.r.selections[0],replace(self.r.selections[1],notices=(n,)))))
    def test_rejected_review_not_outvoted(self):
        rs=reviews_for(self.r,self.p);bad=reviews_for(self.r,self.p,verdict='REJECTED')[0];bad=replace(bad,review_id='second-review',signature='');bad=replace(bad,signature=hmac.new(KEY.secret,bad.signing_bytes(),hashlib.sha256).hexdigest())
        self.assertEqual(self.check('RIGHTS_REVIEW_REJECTED',reviews=rs+(bad,)).status,'BLOCKED')
    def test_uncertain_review(self):self.check('RIGHTS_AUTHORIZATION_REQUIRED',reviews=reviews_for(self.r,self.p,verdict='UNCERTAIN'))
    def test_fractional_confidence_not_approval(self):self.check('RIGHTS_AUTHORIZATION_REQUIRED',reviews=reviews_for(self.r,self.p,confidence=999999))
    def test_bad_signature(self):
        rs=reviews_for(self.r,self.p);self.check('RIGHTS_AUTHORIZATION_REQUIRED',reviews=(replace(rs[0],signature='0'*64),)+rs[1:])
    def test_no_trusted_keys(self):self.check('RIGHTS_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier())
    def test_test_only_key(self):self.check('RIGHTS_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier((replace(KEY,assurance='test_only'),)))
    def test_disabled_key(self):self.check('RIGHTS_AUTHORIZATION_REQUIRED',verifier=ReviewVerifier((replace(KEY,enabled=False),)))
    def test_expired_review(self):
        rs=tuple(replace(r,expires_at=NOW+2) for r in reviews_for(self.r,self.p))
        rs=tuple(replace(r,signature=hmac.new(KEY.secret,r.signing_bytes(),hashlib.sha256).hexdigest()) for r in rs)
        self.check('RIGHTS_AUTHORIZATION_REQUIRED',as_of=NOW+2,reviews=rs)
    def test_review_wrong_request(self):
        rs=reviews_for(self.r,self.p);self.check('RIGHTS_AUTHORIZATION_REQUIRED',r=replace(self.r,job_id='different-job'),reviews=rs)
    def test_review_wrong_policy(self):
        rs=reviews_for(self.r,self.p);self.check('RIGHTS_AUTHORIZATION_REQUIRED',p=replace(self.p,policy_id='different-policy'),reviews=rs)
    def test_wrong_review_evidence(self):
        rs=reviews_for(self.r,self.p);self.check('RIGHTS_AUTHORIZATION_REQUIRED',reviews=(replace(rs[0],evidence_ids=('lesson',)),)+rs[1:])
    def test_unexpected_review(self):
        rs=reviews_for(self.r,self.p);self.check('RIGHTS_UNEXPECTED_REVIEW',reviews=(replace(rs[0],subject_id='wrong-subject'),)+rs[1:])
    def test_duplicate_reviews_rejected(self):
        rs=reviews_for(self.r,self.p)
        with self.assertRaises(ContractError):run(self.r,self.root,self.p,reviews=rs+(rs[0],))
    def test_exception_needs_separate_review(self):
        p=self.grant(basis='EXCEPTION');rs=tuple(x for x in reviews_for(self.r,p) if x.purpose!='inference');self.check('RIGHTS_AUTHORIZATION_REQUIRED',p=p,reviews=rs)
    def test_exception_review_cannot_override_denied_operation(self):self.check('RIGHTS_OPERATION_NOT_GRANTED',p=self.grant(basis='EXCEPTION',operations=('READ',)))
    def test_purchase_origin_does_not_grant(self):self.check('RIGHTS_OPERATION_NOT_GRANTED',p=self.grant(operations=('READ',)))
    def test_training_needs_separate_permission(self):
        p=replace(self.p,requirements=tuple(replace(u,operations=u.operations+('TRAIN',)) for u in self.p.requirements));self.check('RIGHTS_OPERATION_NOT_GRANTED',p=p)
    def test_retrieval_needs_separate_permission(self):
        p=replace(self.p,requirements=tuple(replace(u,operations=u.operations+('RETRIEVE',)) for u in self.p.requirements));self.check('RIGHTS_OPERATION_NOT_GRANTED',p=p)
    def test_additional_voice_rights(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],dimensions=('COPYRIGHT','VOICE'))));self.check('RIGHTS_DIMENSION_NOT_GRANTED',p=p)
    def test_unknown_origin_no_auto_clearance(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],origin='UNKNOWN')));self.check('RIGHTS_ORIGIN_UNKNOWN',p=p)
    def test_license_label_unknown(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],license_expression='NOASSERTION')));self.check('RIGHTS_EXPRESSION_UNKNOWN',p=p)
    def test_upstream_permission_not_inherited_automatically(self):
        p=replace(self.p,requirements=(replace(self.p.requirements[0],operations=('READ',)),self.p.requirements[1]));self.check('RIGHTS_DERIVED_PERMISSION_GAP',p=p)
    def test_wrong_output_license(self):self.check('RIGHTS_OUTPUT_LICENSE_NOT_APPROVED',p=self.grant(allowed_output_licenses=('LicenseRef-Other',)))
    def test_allowed_output_license(self):self.assertEqual(run(self.r,self.root,self.grant(allowed_output_licenses=('LicenseRef-Output',))).status,'CHECKS_PASSED')
    def test_snapshot_binding(self):self.check('RIGHTS_SNAPSHOT_BINDING',p=replace(self.p,snapshot_digest='1'*64))
    def test_extra_snapshot_file(self):
        (self.root/'extra.bin').write_bytes(b'extra');self.check('AUDIT_SNAPSHOT_FILE_SET')
    def test_missing_snapshot_file(self):
        (self.root/'assets/diagram.txt').unlink();self.check('AUDIT_SNAPSHOT_FILE_SET')
    def test_changed_source_bytes(self):
        p=self.root/'source/book.txt';b=p.read_bytes();p.write_bytes(b[:-1]+b'!');self.check('ARTIFACT_HASH_MISMATCH')
    def test_changed_license_bytes(self):
        p=self.root/'rights/asset-terms.txt';p.write_bytes(b'altered terms');self.check('ARTIFACT_SIZE_MISMATCH')
    def test_symlink_snapshot_file(self):
        p=self.root/'assets/diagram.txt';p.unlink();p.symlink_to(self.root/'source/book.txt');self.check('AUDIT_UNSAFE_ENTRY')
    def test_hardlink_snapshot_file(self):
        p=self.root/'assets/diagram.txt';p.unlink();os.link(self.root/'source/book.txt',p);self.check('AUDIT_UNSAFE_ENTRY')
    def test_symlink_root(self):
        p=Path(self.tmp.name)/'alias';p.symlink_to(self.root);result=run(self.r,p,self.p);self.assertIn('AUDIT_SNAPSHOT_ROOT',codes(result))
    def test_status_future(self):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(observed_at=NOW+1));self.check('RIGHTS_STATUS_STALE',r,p)
    def test_status_old(self):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(observed_at=NOW-3601));self.check('RIGHTS_STATUS_STALE',r,p)
    def test_status_missing_entry(self):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(grants=('source-grant',)));self.check('RIGHTS_STATUS_COVERAGE',r,p)
    def test_status_repeated_entry(self):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(grants=('source-grant','source-grant')));self.check('RIGHTS_STATUS_DUPLICATE_OR_UNKNOWN',r,p)
    def test_status_unknown_value(self):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(state='GRANTED_BY_AI'));self.check('RIGHTS_STATUS_VALUE',r,p)
    def test_status_duplicate_json_key(self):
        data=b'{"schema_version":"x","schema_version":"y","observed_at":10000,"grants":[]}'
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',data);self.assertEqual(run(r,self.root,p).status,'BLOCKED')
    def test_scope_expired(self):self.check('RIGHTS_USE_WINDOW_ENDED',as_of=NOW+101)
    def test_valid_worldwide_scope(self):self.assertEqual(run(self.r,self.root,replace(self.p,territories=('IN','US','GB'))).status,'CHECKS_PASSED')
    def test_missing_source_inventory(self):
        mats=(replace(self.p.materials[0],category='ASSET'),self.p.materials[1]);self.check('RIGHTS_SOURCE_INVENTORY_INCOMPLETE',p=replace(self.p,materials=mats))
    def test_terms_missing_ref(self):self.check('RIGHTS_GRANT_DOCUMENT_MISSING',p=self.grant(evidence_ids=('missing-terms',)))
    def test_status_cannot_be_grant_document(self):self.check('RIGHTS_STATUS_NOT_GRANT',p=self.grant(evidence_ids=('rights-status',)))
    def test_source_cannot_be_notice_output(self):
        p=replace(self.p,requirements=(self.p.requirements[0],replace(self.p.requirements[1],notice_artifact_ids=('source',))));self.check('RIGHTS_NOTICE_ROLE',p=p)
    def test_material_missing_ref(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],artifact_id='missing-asset')));self.check('RIGHTS_MATERIAL_BYTES_MISSING',p=p)
    def test_wrong_source_role(self):
        p=replace(self.p,materials=(replace(self.p.materials[0],artifact_id='terms-source'),self.p.materials[1]));self.check('RIGHTS_SOURCE_ROLE_MISMATCH',p=p)
    def test_missing_output_ref(self):
        p=replace(self.p,requirements=(self.p.requirements[0],replace(self.p.requirements[1],output_artifact_id='missing')));self.check('RIGHTS_OUTPUT_BYTES_MISSING',p=p)
    def test_no_implicit_notices_generated(self):
        before={p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()};run(self.r,self.root,self.p)
        self.assertEqual(before,{p.relative_to(self.root).as_posix():p.read_bytes() for p in self.root.rglob('*') if p.is_file()})
    def test_wire_roundtrip(self):
        self.assertEqual(self.r,decode(loads(canonical_bytes(asdict(self.r))),RightsRequest));self.assertEqual(self.p,decode(loads(canonical_bytes(asdict(self.p))),RightsPolicy))
    def test_wire_unknown_fields(self):
        obj=asdict(self.r);obj['product_accepted']=True
        with self.assertRaises(ContractError):decode(loads(canonical_bytes(obj)),RightsRequest)
    def test_boolean_integer_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,commercial=1)
    def test_float_clock_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,planned_until=10010.0)
    def test_empty_territories_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,territories=())
    def test_duplicate_material_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,materials=self.p.materials+(self.p.materials[0],))
    def test_cyclic_lineage_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,materials=(replace(self.p.materials[0],parent_ids=('diagram',)),self.p.materials[1]))
    def test_unknown_parent_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],parent_ids=('missing',))))
    def test_unused_material_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,requirements=self.p.requirements[:1])
    def test_duplicate_notice_rejected(self):
        with self.assertRaises(ContractError):replace(self.r.selections[0],notices=self.r.selections[0].notices*2)
    def test_duplicate_selections_rejected(self):
        with self.assertRaises(ContractError):replace(self.r,selections=self.r.selections*2)
    def test_duplicate_extent_rejected(self):
        with self.assertRaises(ContractError):replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],artifact_id='source')))
    def test_plain_cli(self):
        r=Path(self.tmp.name)/'request.json';p=Path(self.tmp.name)/'policy.json';r.write_bytes(canonical_bytes(asdict(self.r)));p.write_bytes(canonical_bytes(asdict(self.p)))
        proc=subprocess.run([sys.executable,'-B','-m','bie.qa.rights_v2','--request',str(r),'--policy',str(p),'--root',str(self.root),'--as-of',str(NOW)],capture_output=True,timeout=20)
        self.assertEqual(proc.returncode,3,proc.stderr);self.assertEqual(loads(proc.stdout)['status'],'REVIEW_REQUIRED')
    def test_cli_does_not_overwrite(self):
        r=Path(self.tmp.name)/'request.json';p=Path(self.tmp.name)/'policy.json';o=Path(self.tmp.name)/'out.json'
        r.write_bytes(canonical_bytes(asdict(self.r)));p.write_bytes(canonical_bytes(asdict(self.p)));o.write_bytes(b'keep')
        proc=subprocess.run([sys.executable,'-B','-m','bie.qa.rights_v2','--request',str(r),'--policy',str(p),'--root',str(self.root),'--as-of',str(NOW),'--output',str(o)],capture_output=True,timeout=20)
        self.assertEqual(proc.returncode,4);self.assertEqual(o.read_bytes(),b'keep')

# Distinct operator-scope mismatches are separate collected tests, not repeated runs.
for name,changes,code in [
 ('commercial',{'commercial_allowed':False},'RIGHTS_COMMERCIAL_USE_NOT_GRANTED'),
 ('territory',{'territories':('US',)},'RIGHTS_TERRITORY_MISMATCH'),
 ('channel',{'channels':('PRINT',)},'RIGHTS_CHANNEL_MISMATCH'),
 ('grantee',{'grantees':('different-company',)},'RIGHTS_GRANTEE_MISMATCH'),
 ('future_start',{'valid_from':NOW+1},'RIGHTS_GRANT_TIME_WINDOW'),
 ('expiry_during_use',{'valid_until':NOW+99},'RIGHTS_GRANT_TIME_WINDOW'),
 ('expired',{'valid_until':NOW},'RIGHTS_GRANT_TIME_WINDOW'),
 ('adaptation',{'operations':('DISPLAY','DISTRIBUTE')},'RIGHTS_OPERATION_NOT_GRANTED'),
 ('distribution',{'operations':('ADAPT','DISPLAY')},'RIGHTS_OPERATION_NOT_GRANTED')]:
    def test(self,changes=changes,code=code):self.check(code,p=self.grant(**changes))
    setattr(RightsTests,'test_scope_'+name,test)
for state,code in [('REVOKED','RIGHTS_GRANT_INACTIVE'),('SUSPENDED','RIGHTS_GRANT_INACTIVE'),('UNKNOWN','RIGHTS_GRANT_STATUS_UNKNOWN')]:
    def test(self,state=state,code=code):
        r,p=replace_blob(self.r,self.p,self.root,'rights-status',status_blob(state=state));self.check(code,r,p)
    setattr(RightsTests,'test_status_'+state.lower(),test)

class ExpressionTests(unittest.TestCase):
    def test_simple(self):self.assertEqual(single_atom('MIT'),'mit')
    def test_case(self):self.assertEqual(single_atom('mIt'),'mit')
    def test_and(self):self.assertEqual(selected_branch('MIT AND Apache-2.0',('Apache-2.0','MIT')),('apache-2.0','mit'))
    def test_or(self):self.assertEqual(selected_branch('MIT OR Apache-2.0',('MIT',)),('mit',))
    def test_with(self):self.assertEqual(single_atom('GPL-2.0-only WITH Classpath-exception-2.0'),'gpl-2.0-only WITH classpath-exception-2.0')
    def test_precedence(self):self.assertEqual(selected_branch('MIT OR BSD-2-Clause AND Apache-2.0',('BSD-2-Clause','Apache-2.0')),('apache-2.0','bsd-2-clause'))
    def test_nested(self):self.assertEqual(selected_branch('(MIT OR BSD-2-Clause) AND Apache-2.0',('MIT','Apache-2.0')),('apache-2.0','mit'))
    def test_single_grant_not_compound(self):
        with self.assertRaises(ContractError):single_atom('MIT AND Apache-2.0')
    def test_missing_and(self):
        with self.assertRaises(ContractError):selected_branch('MIT AND Apache-2.0',('MIT',))
    def test_not_every_or_branch(self):
        with self.assertRaises(ContractError):selected_branch('MIT OR Apache-2.0',('MIT','Apache-2.0'))
    def test_exception_not_dropped(self):
        with self.assertRaises(ContractError):selected_branch('GPL-2.0-only WITH Classpath-exception-2.0',('GPL-2.0-only',))
    def test_extra_selection(self):
        with self.assertRaises(ContractError):selected_branch('MIT',('MIT','Apache-2.0'))
    def test_repeated_selection(self):
        with self.assertRaises(ContractError):selected_branch('MIT',('MIT','mit'))
    def test_empty_selection(self):
        with self.assertRaises(ContractError):selected_branch('MIT',())
    def test_token_budget(self):
        with self.assertRaises(ContractError):parse(' AND '.join(['MIT']*80))
    def test_depth_budget(self):
        with self.assertRaises(ContractError):parse('('*18+'MIT'+')'*18)

for i,expression in enumerate(['','NOASSERTION','NONE','MIT and Apache-2.0','MIT OR','AND MIT','MIT WITH','(MIT','MIT)','MIT Apache-2.0','(MIT OR BSD) WITH Exc','MIT+','DocumentRef-x:LicenseRef-y','MIT\nOR BSD','MIT / BSD','MIT WITH WITH']):
    def test(self,expression=expression):
        with self.assertRaises(ContractError):parse(expression)
    setattr(ExpressionTests,'test_invalid_expression_%02d'%i,test)

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshot';self.r,self.p=release_fixture(self.root)
    def candidate(self):return ReleaseCandidate('2.0.0','candidate',self.r.snapshot.run_id,self.r.snapshot.revision,tuple(a for a in self.r.snapshot.artifacts if a.role in ('source','video','game')))
    def test_bridge_not_full_pass(self):
        x=prepare_release_evidence(self.r,self.root,self.p,self.candidate(),as_of=NOW,reviews=reviews_for(self.r,self.p),verifier=ReviewVerifier((KEY,)))
        self.assertEqual(x.envelope.status,'NOT_RUN');self.assertFalse(x.envelope.signature);self.assertEqual(x.envelope.gate_id,'rights_and_asset_provenance')
    def test_bridge_detects_failure(self):
        p=replace(self.p,commercial=True,grants=tuple(replace(g,commercial_allowed=False) for g in self.p.grants))
        x=prepare_release_evidence(self.r,self.root,p,self.candidate(),as_of=NOW);self.assertEqual(x.envelope.status,'FAIL')
    def test_bridge_wrong_revision(self):
        with self.assertRaises(ContractError):prepare_release_evidence(self.r,self.root,self.p,replace(self.candidate(),revision='b'*40),as_of=NOW)
    def test_bridge_wrong_artifact(self):
        c=self.candidate();arts=list(c.artifacts);arts[0]=replace(arts[0],sha256='f'*64)
        with self.assertRaises(ContractError):prepare_release_evidence(self.r,self.root,self.p,replace(c,artifacts=tuple(arts)),as_of=NOW)
    def test_bridge_missing_game_use(self):
        p=replace(self.p,requirements=tuple(u for u in self.p.requirements if u.output_artifact_id=='video'))
        with self.assertRaises(ContractError):prepare_release_evidence(self.r,self.root,p,self.candidate(),as_of=NOW)
    def test_exception_all_output_bindings(self):
        p=replace(self.p,grants=(replace(self.p.grants[0],basis='EXCEPTION'),self.p.grants[1]))
        target=review_targets(self.r,p)['inference','rights-exception:source-grant']
        self.assertTrue({'source','video','game','terms-source'}<=set(target))
    def test_expired_window_half_open(self):
        self.assertIn('RIGHTS_USE_WINDOW_ENDED',codes(run(self.r,self.root,self.p,as_of=self.p.planned_until)))
    def test_multiple_outputs_all_required(self):self.assertEqual(run(self.r,self.root,self.p).status,'CHECKS_PASSED')
    def test_game_permission_missing_not_hidden_by_video(self):
        r=replace(self.r,selections=tuple(s for s in self.r.selections if not s.use_id.endswith('game')))
        self.assertIn('RIGHTS_USE_INVENTORY_MISMATCH',codes(run(r,self.root,self.p)))
    def test_source_permissions_cannot_be_self_certified(self):
        rs=tuple(r for r in reviews_for(self.r,self.p) if r.subject_id!='rights-grant:source-grant')
        result=run(self.r,self.root,self.p,reviews=rs);self.assertNotEqual(result.status,'CHECKS_PASSED')

class LicenseIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)/'snapshot';self.r,self.p=make_fixture(self.root)
    def alternative(self,op='OR',select_both=False,inactive=False):
        g=replace(self.p.grants[1],grant_id='alternative',license_atom='LicenseRef-Alternate',obligations=())
        p=replace(self.p,grants=self.p.grants+(g,),materials=(self.p.materials[0],replace(self.p.materials[1],license_expression='LicenseRef-Asset '+op+' LicenseRef-Alternate')))
        raw=json.loads(status_blob(grants=('source-grant','asset-grant','alternative')))
        if inactive:raw['grants'][2]['state']='REVOKED'
        r,p=replace_blob(self.r,p,self.root,'rights-status',canonical_bytes(raw))
        if select_both:r=replace(r,selections=(r.selections[0],replace(r.selections[1],grant_ids=('asset-grant','alternative'))))
        return r,p
    def test_or_selected_branch(self):
        r,p=self.alternative();self.assertEqual(run(r,self.root,p).status,'CHECKS_PASSED')
    def test_unselected_inactive_alternative_not_a_veto(self):
        r,p=self.alternative(inactive=True);self.assertEqual(run(r,self.root,p).status,'CHECKS_PASSED')
    def test_or_cannot_collect_both(self):
        r,p=self.alternative(select_both=True);self.assertIn('RIGHTS_AMBIGUOUS_OR_SELECTION',codes(run(r,self.root,p)))
    def test_and_missing_component(self):
        r,p=self.alternative(op='AND');self.assertIn('RIGHTS_LICENSE_SELECTION_INCOMPLETE',codes(run(r,self.root,p)))
    def test_and_complete(self):
        r,p=self.alternative(op='AND',select_both=True);self.assertEqual(run(r,self.root,p).status,'CHECKS_PASSED')
    def test_and_one_denies_use(self):
        r,p=self.alternative(op='AND',select_both=True);p=replace(p,grants=p.grants[:2]+(replace(p.grants[2],operations=('READ',)),))
        self.assertIn('RIGHTS_OPERATION_NOT_GRANTED',codes(run(r,self.root,p)))
    def test_with_exception_cannot_disappear(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],license_expression='LicenseRef-Asset WITH Special-exception')))
        self.assertIn('RIGHTS_LICENSE_SELECTION_INCOMPLETE',codes(run(self.r,self.root,p)))
    def test_own_claim_still_needs_evidence(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],origin='OWNED_CLAIM')))
        self.assertEqual(run(self.r,self.root,p,signed=False).status,'REVIEW_REQUIRED')
    def test_public_domain_claim_still_needs_evidence(self):
        p=replace(self.p,materials=(self.p.materials[0],replace(self.p.materials[1],origin='PUBLIC_DOMAIN_CLAIM')),grants=(self.p.grants[0],replace(self.p.grants[1],basis='PUBLIC_DOMAIN')))
        self.assertEqual(run(self.r,self.root,p,signed=False).status,'REVIEW_REQUIRED')

class SchemaTests(unittest.TestCase):
    def test_request_schema(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as d:
            r,p=make_fixture(Path(d)/'snapshot');schema=json.loads((Path(__file__).resolve().parents[2]/'docs/qa_section16/batch019/request.schema.json').read_text())
            jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(json.loads(canonical_bytes(asdict(r))),schema)
    def test_policy_schema(self):
        import jsonschema
        with tempfile.TemporaryDirectory() as d:
            r,p=make_fixture(Path(d)/'snapshot');schema=json.loads((Path(__file__).resolve().parents[2]/'docs/qa_section16/batch019/policy.schema.json').read_text())
            jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(json.loads(canonical_bytes(asdict(p))),schema)
    def test_status_schema(self):
        import jsonschema
        schema=json.loads((Path(__file__).resolve().parents[2]/'docs/qa_section16/batch019/status.schema.json').read_text());jsonschema.Draft202012Validator.check_schema(schema);jsonschema.validate(json.loads(status_blob()),schema)
