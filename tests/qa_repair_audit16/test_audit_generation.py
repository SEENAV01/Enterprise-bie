from audit_generation_helpers import *

class GenerationTests(GenerationFixture):
    def test_actual_source_generator_receipt_audited(self):
        result=self.audit();self.assertEqual(result.status,'CHECKS_PASSED',result.to_dict())
    def test_generation_hash_recomputed(self):
        self.mutate_generation(lambda x:x['witness'].update(extra='tampered'));self.assertCode('AUDIT_GENERATION_DIGEST')
    def test_generation_after_bytes_bound(self):
        self.mutate_generation(lambda x:x.update(after_sha256='0'*64));self.assertCode('AUDIT_GENERATION_AFTER')
    def test_generation_before_bytes_bound(self):
        self.mutate_generation(lambda x:x.update(before_sha256='0'*64));self.assertCode('AUDIT_GENERATION_BEFORE')
    def test_generation_size_bound(self):
        self.mutate_generation(lambda x:x.update(generated_bytes=1));self.assertCode('AUDIT_GENERATION_SIZE')
    def test_generation_job_bound(self):
        self.mutate_generation(lambda x:x.update(job_digest='0'*64));self.assertCode('AUDIT_GENERATION_JOB_DIGEST')
    def test_generation_cannot_claim_live_model(self):
        self.mutate_generation(lambda x:x.update(live_model_invoked=True));self.assertCode('AUDIT_GENERATION_SCOPE')
    def test_generation_required_checks_preserved(self):
        self.mutate_generation(lambda x:x.update(required_checks=[]));self.assertCode('AUDIT_GENERATION_CHECKS')
    def test_generation_invalidation_preserved(self):
        self.mutate_generation(lambda x:x.update(invalidated_previous_checks=[]));self.assertCode('AUDIT_GENERATION_INVALIDATION')
    def test_generation_target_failures_preserved(self):
        self.mutate_generation(lambda x:x['witness'].update(target_failure_ids=[]));self.assertCode('AUDIT_GENERATION_TARGETS')
    def test_generation_actual_domain_policy_bytes(self):
        c=self.ctx;obj=asdict(c.dp);obj['policy_id']='changed'
        self.request=replace(self.request,generation=(replace(self.request.generation[0],domain_policy=self.put('domain-policy',obj,'support')),))
        self.assertCode('AUDIT_DOMAIN_POLICY_BYTES')
    def test_generation_actual_limits_bytes(self):
        obj=asdict(self.ctx.limits);obj['max_proof_calls']+=1
        self.request=replace(self.request,generation=(replace(self.request.generation[0],limits=self.put('limits',obj,'support')),))
        self.assertCode('AUDIT_GENERATION_LIMITS_BYTES')
