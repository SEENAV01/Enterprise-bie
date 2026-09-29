from h8_helpers import *

class Rights(Temp):
    def setUp(self):
        super().setUp();self.src=self.root/'rights';self.req,self.rp,self.ip,self.b=rights_fixture(self.src)
        self.s=self.fresh(binding=self.b);self.k.establish(self.s)
    def clearance(self,s=None,ip=None):
        s=s or self.s;ip=ip or self.ip
        return self.k.envelope(s,'rights',clearance_subject(self.req,self.rp,ip,s.binding),
            dict(decision='APPROVE',trust_digest=s.policy.content_digest))
    def run_rights(self,**kw):
        options=dict(as_of=NOW,legacy_reviews=rs.reviews_for(self.req,self.rp),legacy_verifier=rs.ReviewVerifier((rs.KEY,)),session=self.s,clearance=self.clearance())
        options.update(kw)
        return verify_inventory(self.req,self.src,self.rp,self.ip,self.b,**options)
    def test_positive_inventory_calls_inherited(self):
        r=self.run_rights();self.assertTrue(r['technical_checks_clear']);self.assertEqual(r['details']['legacy_result']['status'],'CHECKS_PASSED');self.assertFalse(r['details']['legal_clearance_certified'])
    def test_no_clearance_requires_review(self):
        r=self.run_rights(clearance=None);self.assertIn('H8_QUALIFIED_CLEARANCE_REQUIRED',[f['code'] for f in r['report']['findings']])
    def test_added_file(self):
        (self.src/'hidden.js').write_text('hidden');self.error('H8_FILE_INVENTORY_CHANGED',self.run_rights)
    def test_removed_file(self):
        (self.src/self.ip.files[0]['path']).unlink();self.error('H8_FILE_INVENTORY_CHANGED',self.run_rights)
    def test_mutated_file(self):
        (self.src/self.ip.files[0]['path']).write_text('modified');self.error('H8_FILE_INVENTORY_CHANGED',self.run_rights)
    def test_path_symlink(self):
        p=self.src/self.ip.files[0]['path'];data=p.read_bytes();p.unlink();q=self.root/'other';q.write_bytes(data);p.symlink_to(q)
        with self.assertRaises(ContractError):self.run_rights()
    def test_wrong_inventory_binding(self):
        self.b=replace(self.b,policy_digest='e'*64);self.error('H8_RIGHTS_POLICY_BINDING',self.run_rights)
    def test_wrong_legacy_policy(self):
        self.rp=replace(self.rp,commercial=False);self.error('H8_RIGHTS_POLICY_BINDING',self.run_rights)
    def test_missing_provenance(self):self.error('H8_PROVENANCE_CENSUS',replace,self.ip,provenance=self.ip.provenance[:-1])
    def test_duplicate_provenance_id(self):
        rows=copy.deepcopy(list(self.ip.provenance));rows[0]['artifact_id']=rows[1]['artifact_id'];self.error('H8_PROVENANCE_ALIAS',replace,self.ip,provenance=tuple(rows))
    def test_unknown_parent(self):
        rows=copy.deepcopy(list(self.ip.provenance));rows[0]['parent_ids']=['missing'];self.error('H8_MISSING_PARENT',replace,self.ip,provenance=tuple(rows))
    def test_lineage_cycle(self):
        rows=copy.deepcopy(list(self.ip.provenance));rows[0]['parent_ids']=[rows[0]['artifact_id']];self.error('H8_PROVENANCE_CYCLE',replace,self.ip,provenance=tuple(rows))
    def test_missing_provider(self):self.error('H8_PROVIDER_CENSUS',replace,self.ip,required_provider_ids=('missing-provider',))
    def test_foreign_clearance(self):
        e=self.clearance();e['subject_digest']='a'*64;e=self.k.resign(e);self.error('H8_STATEMENT_SCOPE',self.run_rights,clearance=e)
    def test_revoked_rights(self):
        self.s=self.fresh(binding=self.b);self.k.establish(self.s,epoch=2,revoked=('rights0',));self.error('H8_KEY_REVOKED',self.run_rights)
    def test_caller_time_rejected(self):self.error('H8_RIGHTS_TIME_MISMATCH',self.run_rights,as_of=NOW-1)
    def notices(self,channel='TEXT',method='EXACT_FILE',text_value=None):
        notice=NoticeRequirement('n','book','lesson','Source: Diagnostic Author.',(channel,))
        self.ip=replace(self.ip,notices=(notice,));self.b=replace(self.b,policy_digest=self.ip.content_digest)
        self.s=self.fresh(binding=self.b);self.k.establish(self.s,epoch=2)
        cap=self.root/'capture';cap.mkdir(exist_ok=True)
        a=ref(cap,'notice-capture','notice.txt',b'Source: Diagnostic Author.')
        lesson=next(a for a in self.req.snapshot.artifacts if a.artifact_id=='lesson')
        obs=dict(notice_id='n',channel=channel,output_artifact_id='lesson',output_sha256=lesson.sha256,
            text=text_value or 'Source: Diagnostic Author.',capture=asdict(a),method=method,visible=True,location='credits')
        att=self.k.envelope(self.s,'capture',notice_subject(obs,self.b),dict(decision='APPROVE',trust_digest=self.s.policy.content_digest))
        return cap,{'observation':obs,'attestation':att}
    def test_actual_notice_text(self):
        cap,o=self.notices();r=self.run_rights(observations=(o,),capture_root=cap);self.assertTrue(r['technical_checks_clear'])
    def test_missing_notice(self):
        cap,o=self.notices();r=self.run_rights();self.assertIn('H8_MISSING_NOTICE_COVERAGE',[f['code'] for f in r['report']['findings']])
    def test_text_receipt_not_video(self):
        cap,o=self.notices('VIDEO','EXACT_FILE');r=self.run_rights(observations=(o,),capture_root=cap);self.assertFalse(r['technical_checks_clear'])
    def test_hidden_notice(self):
        cap,o=self.notices();o['observation']['visible']=False;o['attestation']=self.k.envelope(self.s,'capture',notice_subject(o['observation'],self.b),dict(decision='APPROVE',trust_digest=self.s.policy.content_digest))
        r=self.run_rights(observations=(o,),capture_root=cap);self.assertFalse(r['technical_checks_clear'])
    def test_notice_bytes_changed(self):
        cap,o=self.notices();(cap/'notice.txt').write_text('changed');self.error('H8_NOTICE_CAPTURE_CHANGED',self.run_rights,observations=(o,),capture_root=cap)
    def test_duplicate_notice(self):
        cap,o=self.notices();self.error('H8_NOTICE_CENSUS',self.run_rights,observations=(o,o),capture_root=cap)
    def test_notice_output_substitution(self):
        cap,o=self.notices();o['observation']['output_sha256']='f'*64;self.error('H8_NOTICE_OUTPUT_BINDING',self.run_rights,observations=(o,),capture_root=cap)
    def test_capture_approval_not_implied(self):
        cap,o=self.notices();o['attestation']=None;r=self.run_rights(observations=(o,),capture_root=cap)
        self.assertIn('H8_CAPTURE_ATTESTATION_REQUIRED',[f['code'] for f in r['report']['findings']])
    def test_inherited_missing_reviews_not_overridden(self):
        r=self.run_rights(legacy_reviews=());self.assertIn('H8_INHERITED_RIGHTS_REVIEW_REQUIRED',[f['code'] for f in r['report']['findings']])
    def test_material_cannot_be_relabelled(self):
        rows=copy.deepcopy(list(self.ip.provenance));row=next(r for r in rows if r['artifact_id']=='source');row['material_id']='other'
        self.ip=replace(self.ip,provenance=tuple(rows));self.b=replace(self.b,policy_digest=self.ip.content_digest);self.s=self.fresh(binding=self.b);self.k.establish(self.s,epoch=2)
        self.error('H8_MATERIAL_PROVENANCE_BINDING',self.run_rights)
