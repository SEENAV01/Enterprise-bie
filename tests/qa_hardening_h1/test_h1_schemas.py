import json,sys,unittest,tempfile
from pathlib import Path
from jsonschema import Draft202012Validator,ValidationError
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'qa_publication22'))
from pub22_support import Fixture
ROOT=Path(__file__).resolve().parents[2]
class H1SchemaTests(unittest.TestCase):
 def test_all_four_schemas_are_valid(self):
  paths=list((ROOT/'docs/qa_section16/hardening_h1/schemas').glob('*.json'));self.assertEqual(len(paths),4)
  for p in paths:Draft202012Validator.check_schema(json.loads(p.read_text()))
 def test_healthy_terminal_and_unknown_field(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(Path(td));raw=json.loads((f.root/f.native['video_render'].path).read_text())
   v=Draft202012Validator(json.loads((ROOT/'docs/qa_section16/hardening_h1/schemas/terminal-report.schema.json').read_text()));v.validate(raw)
   raw['trust_me']=True
   with self.assertRaises(ValidationError):v.validate(raw)
 def test_nested_severity_schema_is_closed(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(Path(td));raw=json.loads((f.root/f.native['video_render'].path).read_text());raw['checks'][0]['diagnostics']=[{'code':'x','severity':'IGNORE'}]
   v=Draft202012Validator(json.loads((ROOT/'docs/qa_section16/hardening_h1/schemas/terminal-report.schema.json').read_text()))
   with self.assertRaises(ValidationError):v.validate(raw)
 def test_policy_requirement_schema(self):
  with tempfile.TemporaryDirectory() as td:
   f=Fixture(Path(td));raw=f.policy.terminal_requirements[0].to_dict();raw=json.loads(json.dumps(raw))
   v=Draft202012Validator(json.loads((ROOT/'docs/qa_section16/hardening_h1/schemas/terminal-requirement.schema.json').read_text()));v.validate(raw)
