"""Structural-schema regression; graph and authority semantics remain runtime checks."""
from pathlib import Path
from dataclasses import asdict
import json,sys
import jsonschema
from re_helpers import *
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts'))
from build_qa_reasoning16_schemas import schema_for

class SchemaTests(FixtureCase):
    def load(self,name):return json.loads((ROOT/'docs/qa_section16/batch004'/name).read_text())
    def data(self):return json.loads(canonical_bytes(self.request.to_dict()))
    def test_all_schemas_validate_their_own_structure(self):
        for name in ('request.schema.json','policy.schema.json','review.schema.json'):
            with self.subTest(name=name):jsonschema.Draft202012Validator.check_schema(self.load(name))
    def test_request_example_valid(self):jsonschema.validate(self.data(),self.load('request.schema.json'))
    def test_policy_example_valid(self):jsonschema.validate(json.loads(canonical_bytes(self.policy.to_dict())),self.load('policy.schema.json'))
    def test_review_example_valid(self):jsonschema.validate(json.loads(canonical_bytes(asdict(signed_reviews(self.request,self.policy)[0]))),self.load('review.schema.json'))
    def test_schema_generator_reproduces_committed_files(self):
        for cls,name in ((ReasoningRequest,'request.schema.json'),(ReasoningPolicy,'policy.schema.json'),(Review,'review.schema.json')):
            with self.subTest(name=name):self.assertEqual(schema_for(cls),self.load(name))
    def test_missing_required_property_rejected(self):
        d=self.data();del d['source']
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_additional_trust_property_rejected(self):
        d=self.data();d['reviews_are_trusted']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_nested_foreign_property_rejected(self):
        d=self.data();d['steps'][0]['override']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_boolean_integer_rejected(self):
        d=self.data();d['events'][0]['position']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_expression_arity_rejected(self):
        d=self.data();d['statements'][0]['expression']={'op':'not','atom':'','args':[]}
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_unknown_logical_operator_rejected(self):
        d=self.data();d['statements'][0]['expression']['op']='eval'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
    def test_null_collection_rejected(self):
        d=self.data();d['events']=None
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.load('request.schema.json'))
