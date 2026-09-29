from pub22_support import *
import json,subprocess,sys
from pathlib import Path
from jsonschema import Draft202012Validator,ValidationError
ROOT=Path(__file__).resolve().parents[2]
class Interfaces(Case):
    def test_all_five_schemas(self):
        for p in (ROOT/'docs/qa_section16/batch022/schemas').glob('*.json'):Draft202012Validator.check_schema(json.loads(p.read_text()))
        self.assertEqual(len(list((ROOT/'docs/qa_section16/batch022/schemas').glob('*.json'))),5)
    def test_request_schema(self):self.validate('request',self.f.request.to_dict())
    def test_proof_schema(self):self.validate('gate-proof',json.loads((self.root/self.f.ev().report.path).read_text()))
    def test_exit_schema(self):self.validate('section-exit',json.loads((self.root/self.f.request.governance[0].path).read_text()))
    def test_approval_schema(self):self.validate('approval',self.f.approvals()[0].to_dict())
    def test_certificate_schema(self):self.validate('certificate',self.f.issue())
    def validate(self,name,value):
        d=json.loads((ROOT/('docs/qa_section16/batch022/schemas/'+name+'.schema.json')).read_text());v=Draft202012Validator(d);v.validate(value)
        bad=dict(value);bad['unexpected']=True
        with self.assertRaises(ValidationError):v.validate(bad)
    def test_cli_read_only_default_denies(self):
        req=self.root/'request.json';req.write_bytes(canonical_bytes(self.f.request.to_dict()))
        before={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        result=subprocess.run([sys.executable,'-B','-m','bie.qa.publication_v2',str(req),'--root',str(self.root),'--environment','diag','--as-of',str(NOW)],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,3,result.stderr);self.assertEqual(json.loads(result.stdout)['status'],'BLOCKED')
        after={p.relative_to(self.root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in self.root.rglob('*') if p.is_file()}
        self.assertEqual(before,after)
    def test_cli_malformed(self):
        req=self.root/'request.json';req.write_bytes(b'{}')
        result=subprocess.run([sys.executable,'-B','-m','bie.qa.publication_v2',str(req),'--root',str(self.root),'--environment','diag','--as-of',str(NOW)],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(result.returncode,4);self.assertFalse(json.loads(result.stdout)['product_accepted'])
    def raw_mutation(self,payload):
        old=self.f.native['video_render'];new=ref(self.root,old.artifact_id,old.path,payload)
        self.f.proof(lambda d:d.update(source_reports=[new.to_dict()]))
    def test_underlying_fail_cannot_be_wrapped_as_pass(self):
        self.raw_mutation(dict(status='FAIL'));self.blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_underlying_false_cannot_be_wrapped_as_pass(self):
        self.raw_mutation(dict(passed=False));self.blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_underlying_open_gaps_cannot_be_hidden(self):
        self.raw_mutation(dict(gaps=[dict(gap_id='real-gap',status='OPEN')]));self.blocked('UNREGISTERED_TERMINAL_SCHEMA')
    def test_underlying_musthaves_cannot_be_hidden(self):
        self.raw_mutation(dict(open_must_have_ids=['gap']));self.blocked('UNREGISTERED_TERMINAL_SCHEMA')
