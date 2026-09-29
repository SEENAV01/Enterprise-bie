from math_helpers import *
import jsonschema
ROOT=Path(__file__).resolve().parents[2]
class SchemaTests(FixtureCase):
    def schema(self,name):return json.loads((ROOT/'docs/qa_section16/batch005'/(name+'.schema.json')).read_text())
    def test_all_schemas_valid(self):
        for name in ('request','policy','review'):
            with self.subTest(name=name):jsonschema.Draft202012Validator.check_schema(self.schema(name))
    def test_request_shape(self):jsonschema.validate(json.loads(canonical_bytes(self.request.to_dict())),self.schema('request'))
    def test_policy_shape(self):jsonschema.validate(json.loads(canonical_bytes(asdict(self.policy))),self.schema('policy'))
    def test_review_shape(self):jsonschema.validate(json.loads(canonical_bytes(asdict(signed_reviews(self.request,self.policy)[0]))),self.schema('review'))
    def test_extra_field_rejected(self):
        d=json.loads(canonical_bytes(self.request.to_dict()));d['authority']='production'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.schema('request'))
    def test_extra_nested_field_rejected(self):
        d=json.loads(canonical_bytes(self.request.to_dict()));d['formulas'][0]['equation']['left']['pass']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.schema('request'))
    def test_false_type_rejected(self):
        d=json.loads(canonical_bytes(asdict(self.policy)));d['minimum_independent_assessors']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(d,self.schema('policy'))
