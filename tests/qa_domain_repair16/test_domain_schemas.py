from domain_helpers import *
from jsonschema import Draft202012Validator,ValidationError
class SchemaTests(Base):
 def validate(self,name,data):
  s=json.loads((W/'schemas/qa_domain_repair16'/(name+'.schema.json')).read_text());Draft202012Validator.check_schema(s);Draft202012Validator(s).validate(json.loads(canonical_bytes(data)))
 def test_job_schema(self):self.validate('job',asdict(self.context().job))
 def test_limits_schema(self):self.validate('limits',asdict(Limits()))
 def test_receipt_schema(self):self.validate('generation_receipt',self.context().generate().receipt())
 def test_unknown_job_field(self):
  d=asdict(self.context().job);d['command']='shell';self.assertRaises(ValidationError,self.validate,'job',d)
 def test_bad_limits_schema(self):
  d=asdict(Limits());d['max_proof_calls']=0;self.assertRaises(ValidationError,self.validate,'limits',d)
 def test_receipt_acceptance_denied(self):
  d=self.context().generate().receipt();d['product_accepted']=True;self.assertRaises(ValidationError,self.validate,'generation_receipt',d)
 def test_receipt_old_reviews_not_reusable(self):
  d=self.context().generate().receipt();d['previous_candidate_reviews_reusable']=True;self.assertRaises(ValidationError,self.validate,'generation_receipt',d)
 def test_literal_float_limits_denied(self):
  # Semantic Python loading is stricter than JSON Schema's mathematical integer type.
  self.assertRaises(ContractError,Limits,max_proof_calls=1.0)
