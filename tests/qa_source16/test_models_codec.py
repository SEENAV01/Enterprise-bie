import json
from dataclasses import asdict, replace
from source_helpers import *
from bie.qa.source_v2.codec import load_request, loads, request_from_dict, load_assessments, MAX_REQUEST_JSON_BYTES
from bie.qa.source_v2.models import Block

class ModelTests(FixtureCase):
    def test_request_identity_changes_with_content(self):
        self.assertNotEqual(self.request.content_digest,replace(self.request,run_id='other').content_digest)
    def test_bool_is_not_integer(self):
        with self.assertRaises(ContractError):replace(self.request.claims[0],start=False)
    def test_nonhex_source_hash_rejected(self):
        with self.assertRaises(ContractError):replace(self.request.blocks[0],source_sha256='g'*64)
    def test_foreign_schema_rejected(self):
        with self.assertRaises(ContractError):replace(self.request,schema_version='2.0.0')
    def test_empty_collections_rejected(self):
        for name in ('sources','outputs','blocks','claims'):
            with self.subTest(name=name),self.assertRaises(ContractError):replace(self.request,**{name:()})
    def test_duplicate_ids_rejected(self):
        for name in ('sources','outputs','blocks','claims','citations'):
            with self.subTest(name=name),self.assertRaises(ContractError):replace(self.request,**{name:getattr(self.request,name)*2})
    def test_duplicate_citation_span_alias_rejected(self):
        with self.assertRaises(ContractError):replace(self.request,citations=self.request.citations+(replace(self.request.citations[0],citation_id='alias'),))
    def test_duplicate_claim_span_alias_rejected(self):
        with self.assertRaises(ContractError):replace(self.request,claims=self.request.claims+(replace(self.request.claims[0],claim_id='alias'),))
    def test_frozen_input(self):
        from dataclasses import FrozenInstanceError
        with self.assertRaises(FrozenInstanceError):self.request.run_id='edited'
    def test_unicode_surrogate_and_nul_rejected(self):
        for value in ('\ud800','hello\x00world'):
            with self.subTest(value=repr(value)),self.assertRaises(ContractError):replace(self.request.blocks[0],text=value)
    def test_invalid_geometries_rejected(self):
        for box in ((0,0,0,100),(-1,0,1,1),(0,0,1000001,100),(False,0,1,1),[0,0,1,1]):
            with self.subTest(box=box),self.assertRaises(ContractError):replace(self.request.blocks[0],box_ppm=box)
    def test_utf8_only_one_page(self):
        with self.assertRaises(ContractError):replace(self.request.sources[0],page_count=2)
    def test_policy_floors_cannot_be_lowered(self):
        for field in ('minimum_confidence_ppm','minimum_extraction_confidence_ppm'):
            with self.subTest(field=field),self.assertRaises(ContractError):replace(self.policy,**{field:899999})
    def test_duplicate_output_scope_rejected(self):
        with self.assertRaises(ContractError):replace(self.policy,expected_output_ids=('narration','narration'))
    def test_artifact_role_not_implicitly_coerced(self):
        with self.assertRaises(ContractError):replace(self.request.outputs[0],artifact=self.request.sources[0].artifact)
    def test_input_lists_not_immutable_tuples(self):
        with self.assertRaises(ContractError):replace(self.request,claims=list(self.request.claims))
    def test_report_is_deterministic_and_not_accepted(self):
        first=self.check();second=self.check()
        self.assertEqual(first,second);self.assertFalse(first.provenance.product_accepted)
        self.assertEqual(first.provenance.content_digest,second.provenance.content_digest)

class CodecTests(FixtureCase):
    def test_wire_roundtrip(self):
        self.assertEqual(load_request(canonical_bytes(self.request.to_dict())),self.request)
    def test_unknown_request_fields_rejected(self):
        data=json.loads(canonical_bytes(self.request.to_dict()));data['trusted']=True
        with self.assertRaises(ContractError):request_from_dict(data)
    def test_unknown_nested_fields_rejected(self):
        data=json.loads(canonical_bytes(self.request.to_dict()));data['claims'][0]['grounded']=True
        with self.assertRaises(ContractError):request_from_dict(data)
    def test_missing_field_rejected(self):
        data=json.loads(canonical_bytes(self.request.to_dict()));del data['claims'][0]['kind']
        with self.assertRaises(ContractError):request_from_dict(data)
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(ContractError):loads(b'{"pass":false,"pass":true}')
    def test_nonfinite_and_float_rejected(self):
        for value in (b'NaN',b'Infinity',b'-Infinity',b'0.5',b'1e6'):
            with self.subTest(value=value),self.assertRaises(ContractError):loads(value)
    def test_bad_utf8_rejected(self):
        with self.assertRaises(ContractError):loads(b'\xff')
    def test_bad_json_rejected(self):
        with self.assertRaises(ContractError):loads(b'{')
    def test_deeply_nested_json_rejected(self):
        with self.assertRaises(ContractError):loads(b'['*80+b'0'+b']'*80)
    def test_oversized_json_rejected_before_parse(self):
        with self.assertRaises(ContractError):loads(b' '*(MAX_REQUEST_JSON_BYTES+1))
    def test_source_boolean_page_rejected(self):
        d=json.loads(canonical_bytes(self.request.to_dict()));d['sources'][0]['page_count']=True
        with self.assertRaises(ContractError):request_from_dict(d)
    def test_assessment_roundtrip(self):
        a=signed(self.request,self.policy)
        self.assertEqual(load_assessments(canonical_bytes([asdict(a)])),(a,))
    def test_assessment_cannot_bring_key_secret(self):
        d=asdict(signed(self.request,self.policy));d['secret']='do-not-trust'
        with self.assertRaises(ContractError):load_assessments(canonical_bytes([d]))
