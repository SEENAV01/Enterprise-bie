from h8_helpers import *
import subprocess

class Memory(Temp):
    def setUp(self):
        super().setUp();self.src,self.p,self.b,self.rc=memory_fixture(self.root,self.k,self.clock)
        self.s=self.fresh(binding=self.b);self.k.establish(self.s)
    def envelopes(self):return self.k.roles(self.s,correction_subject(self.p,self.b),('review','memory'))
    def export(self,**kw):
        args=dict(rights=self.rc,session=self.s,envelopes=self.envelopes());args.update(kw)
        return prepare_export(self.src,self.root/'export.json',self.p,self.b,**args)
    def record(self):self.export();return strict_object((self.root/'export.json').read_bytes())
    def reuse(self,r,**kw):
        subject=digest({'record_digest':r['content_digest'],'binding':asdict(self.b),'operation':'reuse_candidate'})
        args=dict(session=self.s,envelopes=self.k.roles(self.s,subject,('review','memory')),rights=self.rc,current_source_sha256=self.p.source.sha256,source_root=self.src);args.update(kw)
        return check_reuse(r,self.p,self.b,**args)
    def test_actual_rights_safe_export(self):
        result=self.export();self.assertEqual(result['status'],'DIAGNOSTIC_EXPORT');self.assertFalse(result['training_performed']);self.assertFalse(result['live_memory_mutated'])
    def test_source_original_unchanged(self):
        before=inventory(self.src);self.export();self.assertEqual(before,inventory(self.src))
    def test_export_no_overwrite(self):
        self.export()
        with self.assertRaises(FileExistsError):self.export()
    def test_missing_independent_approval(self):self.error('H8_ROLE_CENSUS',self.export,envelopes=self.envelopes()[:1])
    def test_changed_correction_bytes(self):
        (self.src/self.p.after.path).write_text('changed');self.error('H8_CORRECTION_BYTES_CHANGED',self.export)
    def test_changed_source_bytes(self):
        (self.src/self.p.source.path).write_text('changed');self.error('H8_CORRECTION_BYTES_CHANGED',self.export)
    def test_changed_validation_bytes(self):
        (self.src/self.p.validation.path).write_text('{}');self.error('H8_CORRECTION_BYTES_CHANGED',self.export)
    def bad_validation(self,fn):
        v=strict_object((self.src/self.p.validation.path).read_bytes());fn(v)
        a=ref(self.src,'validation',self.p.validation.path,canonical_bytes(v));self.p=replace(self.p,validation=a);self.b=replace(self.b,policy_digest=self.p.content_digest)
    def test_candidate_regression_rejected(self):
        self.bad_validation(lambda v:v['cases'][1].update(after='FAIL'));self.error('H8_CORRECTION_REGRESSION',inspect_correction,self.src,self.p,self.b)
    def test_target_failure_not_reproduced(self):
        self.bad_validation(lambda v:v['cases'][0].update(before='PASS'));self.error('H8_CORRECTION_FAILURE_NOT_REPRODUCED',inspect_correction,self.src,self.p,self.b)
    def test_missing_case_rejected(self):
        self.bad_validation(lambda v:v['cases'].pop());self.error('H8_CORRECTION_CASE_CENSUS',inspect_correction,self.src,self.p,self.b)
    def test_lost_condition_rejected(self):
        self.bad_validation(lambda v:v.update(conditions_preserved=False));self.error('H8_CORRECTION_LOST_CONDITIONS',inspect_correction,self.src,self.p,self.b)
    def test_wrong_revision_rejected(self):
        self.bad_validation(lambda v:v.update(revision='f'*40));self.error('H8_CORRECTION_VALIDATION_BINDING',inspect_correction,self.src,self.p,self.b)
    def test_old_approval_not_for_new_plan(self):
        old=self.envelopes();self.p=replace(self.p,audience='grade5');self.b=replace(self.b,policy_digest=self.p.content_digest);self.s=self.fresh(binding=self.b);self.k.establish(self.s)
        self.error('H8_STATEMENT_SCOPE',self.export,envelopes=old)
    def test_rights_review_missing(self):
        rc=replace(self.rc,clearance=None);self.error('H8_CORRECTION_RIGHTS_NOT_CLEARED',self.export,rights=rc)
    def test_expired_rights_session(self):
        self.clock[0]=31_000_000_000;self.error('H8_SESSION_EXPIRED',self.export)
    def test_reuse_requires_revalidation(self):
        r=self.record();v=self.reuse(r);self.assertEqual(v['status'],'REVALIDATION_REQUIRED');self.assertFalse(v['can_execute_or_release'])
    def test_reuse_source_changed(self):
        r=self.record();self.error('H8_REUSE_STALE_SOURCE',self.reuse,r,current_source_sha256='a'*64)
    def test_reuse_record_tampered(self):
        r=self.record();r['correction_text']='wrong';self.error('H8_REUSE_RECORD_CHANGED',self.reuse,r)
    def test_reuse_tampered_and_rehashed(self):
        r=self.record();r['correction_text']='wrong';r['content_digest']=digest({k:v for k,v in r.items() if k!='content_digest'});self.error('H8_REUSE_CORRECTION_CHANGED',self.reuse,r)
    def test_reuse_old_signatures(self):
        r=self.record();self.error('H8_STATEMENT_SCOPE',self.reuse,r,envelopes=self.envelopes())
    def test_reuse_gate_removal(self):
        r=self.record();r['rerun_gates']=[];r['content_digest']=digest({k:v for k,v in r.items() if k!='content_digest'});self.error('H8_REUSE_GATE_WAIVER',self.reuse,r)
    def test_reuse_training_flag_cannot_change(self):
        r=self.record();r['training_allowed']=True;r['content_digest']=digest({k:v for k,v in r.items() if k!='content_digest'});self.error('H8_REUSE_SCOPE_CHANGED',self.reuse,r)
    def test_context_change_rejected(self):
        r=self.record();self.p=replace(self.p,audience='other');self.error('H8_REUSE_CONTEXT_CHANGED',self.reuse,r)
    def test_gate_waiver_policy_rejected(self):self.error('H8_REUSE_GATE_WAIVER',replace,self.p,rerun_gates=('source',))
    def test_no_change_not_correction(self):self.error('H8_CORRECTION_ALIAS',replace,self.p,before=self.p.after)
    def test_limit(self):
        self.p=replace(self.p,max_export_bytes=1);self.b=replace(self.b,policy_digest=self.p.content_digest)
        self.error('H8_CORRECTION_EXPORT_LIMIT',inspect_correction,self.src,self.p,self.b)
    def test_readonly_cli(self):
        q=self.root/'request.json';q.write_bytes(canonical_bytes({'plan':asdict(self.p),'binding':asdict(self.b)}))
        before=inventory(self.src);r=subprocess.run([sys.executable,'-B','-m','bie.qa.assurance_quality_v2',str(q),'--root',str(self.src)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'OAI_IS_JUPYTER_KERNEL':'0'})
        self.assertEqual(r.returncode,3,r.stderr.decode());self.assertEqual(json.loads(r.stdout)['status'],'REVIEW_REQUIRED');self.assertEqual(inventory(self.src),before)

    def test_reuse_reads_actual_current_source(self):
        r=self.record();(self.src/self.p.source.path).write_text('Source changed after approval')
        self.error('H8_REUSE_STALE_SOURCE',self.reuse,r)
