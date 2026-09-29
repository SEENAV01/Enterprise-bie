from h3_support import *
from copy import deepcopy
import subprocess,jsonschema
ROOT=Path(__file__).resolve().parents[2]

class SchemaChecks(TempCase):
    def values(self):
        dp,b,ref,snap,source,blocks=doc_fixture(self.root);r=verify_document(snap,ref,self.root,b,dp)
        cp,cb,c,p,cr,pr=calibration_fixture(self.root);rp,rb,g,l,lr=readiness_fixture(self.root)
        cfg=Provider('p','m','v');task=AssessmentTask('task',b,(save(self.root,'text.txt',b'Source text.'),),('check',),(('check','Read the source.'),))
        def unavailable(w,t):raise TransientAssessorError()
        ar,receipt=AssessorRegistry(((cfg,unavailable),)).run('p',task,self.root)
        diag=dict(schema_version='bie.qa.learner-diagnostic/1',observation_id='obs',learner_id='learner1',concept_id='a',assessed_at=NOW-1,policy_digest=rp.content_digest,scores={'knowledge':900000,'application':900000},reported_mastery=True,provenance_mode='diagnostic')
        return dict(report=r.to_dict(),document=snap,assessor_execution=receipt,calibration_corpus=c,calibration_predictions=p,lesson_scope=l,learner_diagnostic=diag)
    def schema(self,name):return json.loads((ROOT/'schemas/qa_section16_h3'/(name+'.schema.json')).read_text())

# Each generated method has a distinct schema and assertion; counts are actual tests.
for name in ('report','document','assessor_execution','calibration_corpus','calibration_predictions','lesson_scope','learner_diagnostic'):
    def positive(self,n=name):jsonschema.Draft202012Validator(self.schema(n)).validate(json.loads(canonical_bytes(self.values()[n])))
    def negative(self,n=name):
        val=json.loads(canonical_bytes(self.values()[n]));val['untrusted_authorization']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.Draft202012Validator(self.schema(n)).validate(val)
    setattr(SchemaChecks,'test_'+name+'_actual_structure',positive)
    setattr(SchemaChecks,'test_'+name+'_unknown_field_rejected',negative)

class CommandChecks(TempCase):
    def setUp(self):
        super().setUp();p,b,ref,s,source,blocks=doc_fixture(self.root)
        for name,value in (('policy',asdict(p)),('binding',asdict(b)),('ref',asdict(ref))):save(self.root,name+'.json',value)
    def cmd(self):return [sys.executable,'-B','-m','bie.qa.native_quality_v2','inspect-document','--root',str(self.root),'--source-ref',str(self.root/'ref.json'),'--policy',str(self.root/'policy.json'),'--binding',str(self.root/'binding.json'),'--output',str(self.root/'result.json')]
    def test_real_cli_read_only_review(self):
        p=subprocess.run(self.cmd(),cwd=ROOT,capture_output=True,timeout=10);self.assertEqual(p.returncode,3,p.stderr);self.assertEqual(json.loads((self.root/'result.json').read_text())['report']['status'],'REVIEW_REQUIRED')
    def test_cli_preserves_existing_output(self):
        (self.root/'result.json').write_bytes(b'existing');p=subprocess.run(self.cmd(),cwd=ROOT,capture_output=True,timeout=10);self.assertEqual(p.returncode,4);self.assertEqual((self.root/'result.json').read_bytes(),b'existing')
