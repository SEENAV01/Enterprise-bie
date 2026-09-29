from h3_support import *
from bie.qa.source_v2.models import Claim

class KnowledgeChecks(TempCase):
    def setUp(self):super().setUp();self.q,self.sp,self.p,self.b,self.links,self.refs=knowledge_fixture(self.root)
    def run_check(self):return inspect_inventory(self.q,self.root,self.sp,self.p,self.links,self.refs,binding=self.b,as_of=NOW)[0]
    def test_real_native_claim_identity(self):self.assertEqual(self.q.claims[0].claim_id,'p00001-r00001:c0')
    def test_native_grounded_flag_not_truth(self):
        r,d=inspect_inventory(self.q,self.root,self.sp,self.p,self.links,self.refs,binding=self.b,as_of=NOW)
        self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertFalse(d['source_entailment_is_truth'])
    def test_no_fabricated_atoms(self):self.assertIn('OPEN_WORLD_CLAIMS_NOT_FABRICATED_AS_ATOMS',codes(self.run_check()))
    def test_independent_reference_reread(self):
        (self.root/'reference.txt').write_text('tampered')
        with self.assertRaises(ContractError):self.run_check()
    def test_citation_output_tamper_blocks(self):
        (self.root/'output.txt').write_text('Other words')
        self.assertEqual(self.run_check().status,'BLOCKED')
    def test_missing_required_claim(self):
        self.p=replace(self.p,expected_claim_ids=self.p.expected_claim_ids+('missing-claim',));self.b=bound(self.p)
        self.blocked(self.run_check(),'CLAIM_INVENTORY_MISMATCH')
    def test_missing_critical_facet(self):self.links={};self.blocked(self.run_check(),'MISSING_CRITICAL_FACET')
    def test_extra_facet(self):self.links['extra']=self.links['facet-1'];self.blocked(self.run_check(),'FACET_INVENTORY_MISMATCH')
    def test_duplicate_facet_claim_does_not_inflate(self):self.links['facet-1']=self.links['facet-1']*2;self.blocked(self.run_check(),'MISSING_CRITICAL_FACET')
    def test_unknown_facet_claim(self):self.links['facet-1']=('unknown',);self.blocked(self.run_check(),'MISSING_CRITICAL_FACET')
    def test_unknown_facet_source(self):
        f=replace(self.p.facets[0],source_block_ids=('unknown',));self.p=replace(self.p,facets=(f,));self.b=bound(self.p)
        self.blocked(self.run_check(),'FACET_SOURCE_MISSING')
    def test_missing_source_condition(self):
        f=replace(self.p.facets[0],required_conditions=('in a vacuum',));self.p=replace(self.p,facets=(f,));self.b=bound(self.p)
        self.blocked(self.run_check(),'CONDITION_NOT_IN_SOURCE')
    def test_erased_qualifier(self):
        c=self.q.claims[0];short='Force is proportional to mass';out=replace(self.q.outputs[0],artifact=save(self.root,'output.txt',short.encode(),identifier='output-text'))
        c=replace(c,text=short,end=len(short),output_sha256=out.artifact.sha256);self.q=replace(self.q,outputs=(out,),claims=(c,))
        self.blocked(self.run_check(),'LOST_SOURCE_CONDITION')
    def test_missing_reference_inventory(self):self.refs=();self.blocked(self.run_check(),'REFERENCE_INVENTORY_MISMATCH')
    def test_source_cannot_be_its_own_independent_reference(self):
        r=self.q.sources[0].artifact;self.refs=(replace(r,artifact_id='independent-reference'),)
        self.blocked(self.run_check(),'REFERENCE_NOT_BYTE_INDEPENDENT')
    def test_duplicate_reference_ids(self):
        self.refs*=2
        with self.assertRaisesRegex(ContractError,'DUPLICATE_REFERENCE_ID'):self.run_check()
    def test_reference_aliases_with_same_bytes(self):
        self.p=replace(self.p,independent_reference_ids=('independent-reference','ref2'));self.b=bound(self.p);self.refs+=(replace(self.refs[0],artifact_id='ref2'),)
        self.blocked(self.run_check(),'REFERENCE_NOT_BYTE_INDEPENDENT')
    def test_policy_binding(self):
        self.b=replace(self.b,policy_digest='f'*64)
        with self.assertRaisesRegex(ContractError,'KI_POLICY_BINDING'):self.run_check()
    def test_run_binding(self):
        self.b=replace(self.b,run_id='foreign')
        with self.assertRaisesRegex(ContractError,'KI_REQUEST_BINDING'):self.run_check()
    def test_native_selection_requires_original_text(self):
        with self.assertRaisesRegex(ContractError,'KI_SELECTED_TEXT_NOT_IN_SOURCE'):native_claims(self.q.blocks[0],('invented fact',))
    def test_native_selection_cannot_trim_conditions(self):
        with self.assertRaisesRegex(ContractError,'KI_SELECTED_TEXT_NOT_IN_SOURCE'):native_claims(self.q.blocks[0],(' '+SENTENCE,))
    def test_multiple_domain_no_math_claim(self):
        q,sp,p,b,links,refs=knowledge_fixture(self.root,'Leaves exchange gases through stomata.')
        r,d=inspect_inventory(q,self.root,sp,p,links,refs,binding=b,as_of=NOW);self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertEqual(d['normalizations'],[])
    def test_output_placement_is_exact(self):
        q=self.q;c=q.claims[0]
        with self.assertRaisesRegex(ContractError,'KI_OUTPUT_SPAN'):
            source_request(q.sources[0],q.blocks,q.outputs[0],SENTENCE,native_claims(q.blocks[0],(SENTENCE,)),{c.claim_id:(1,len(SENTENCE))},self.b)
    def test_export_inspects_source_output_reference(self):self.assertEqual(len(self.run_check().inspected),3)
