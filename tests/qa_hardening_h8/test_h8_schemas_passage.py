from h8_helpers import *
import jsonschema,subprocess

class Schemas(Temp):
    def schema(self,name):return json.loads((ROOT/'hardening/section16_h8/schemas'/f'{name}.schema.json').read_text())
    def test_five_structural_schemas(self):
        paths=list((ROOT/'hardening/section16_h8/schemas').glob('*.json'));self.assertEqual(len(paths),5)
        for p in paths:jsonschema.Draft202012Validator.check_schema(json.loads(p.read_text()))
    def test_envelope_schema_positive(self):
        e=self.k.envelope(self.session,'review','e'*64,{'decision':'APPROVE'});jsonschema.validate(e,self.schema('signed_assurance'))
    def test_envelope_schema_no_secret(self):
        e=self.k.envelope(self.session,'review','e'*64,{});e['secret']='NOT-ALLOWED'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(e,self.schema('signed_assurance'))
    def test_schema_boolean_not_timestamp(self):
        e=self.k.envelope(self.session,'review','e'*64,{});e['created_at']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(e,self.schema('signed_assurance'))
    def test_notice_shape(self):
        a=ArtifactRef('capture','capture.txt','a'*64,1,'report')
        v=dict(notice_id='n',channel='TEXT',output_artifact_id='lesson',output_sha256='b'*64,text='credits',capture=asdict(a),method='EXACT_FILE',visible=True,location='end')
        jsonschema.validate(v,self.schema('notice_observation'))
        v['visible']='true'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,self.schema('notice_observation'))
    def test_stage_result_shape(self):
        v=dict(schema_version='bie.qa.book-stage-result/1',stage='BI',run_id='run',execution_id='e',request_digest='a'*64,source_digest='b'*64,checks=[dict(check_id='a',status='PASS')]);jsonschema.validate(v,self.schema('stage_result'))
        v['checks'][0]['status']='SKIPPED'
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,self.schema('stage_result'))
    def test_correction_shape(self):
        v=dict(schema_version='bie.qa.correction-validation/1',source_sha256='a'*64,before_sha256='b'*64,after_sha256='c'*64,revision='a'*40,cases=[dict(case_id='a',before='FAIL',after='PASS')],conditions_preserved=True);jsonschema.validate(v,self.schema('correction_validation'))
        v['cases']=[]
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,self.schema('correction_validation'))
    def test_no_report_acceptance_flag(self):
        v=outcome('BIE-QA-HARD-035',self.binding,{});jsonschema.validate(v,self.schema('assurance_report'));v['production_authorized']=True
        with self.assertRaises(jsonschema.ValidationError):jsonschema.validate(v,self.schema('assurance_report'))
    def test_cli_invalid_request(self):
        p=self.root/'invalid.json';p.write_text('{}');r=subprocess.run([sys.executable,'-B','-m','bie.qa.assurance_quality_v2',str(p),'--root',str(self.root)],cwd=ROOT,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env={**os.environ,'OAI_IS_JUPYTER_KERNEL':'0'})
        self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['status'],'BLOCKED')

class NativePassage(Temp):
    def pdf(self,content):
        import pymupdf
        d=pymupdf.open();p=d.new_page();p.insert_text((40,60),content);data=d.tobytes();d.close()
        return ref(self.root,'source','source.pdf',data,'source')
    def test_actual_native_text_pdf_and_claims(self):
        a=self.pdf('A square has four sides.');r=inspect_source_passage(self.root,a,page=1,quote='A square has four sides.',run_id='passage',revision='a'*40)
        self.assertEqual(r['native_claim']['text'],'A square has four sides.');self.assertTrue(r['native_evidence_is_identifier_link_only']);self.assertFalse(r['full_real_book_e2e']);self.assertEqual(r['stage_status']['COMP'],'NOT_RUN')
    def test_unsupported_quote_rejected(self):
        a=self.pdf('A square has four sides.');self.error('H8_SOURCE_PASSAGE_NOT_FOUND',inspect_source_passage,self.root,a,page=1,quote='A square has three sides.',run_id='passage',revision='a'*40)
    def test_ambiguous_quote_rejected(self):
        a=self.pdf('Repeated text. Repeated text.');self.error('H8_SOURCE_PASSAGE_AMBIGUOUS',inspect_source_passage,self.root,a,page=1,quote='Repeated text.',run_id='passage',revision='a'*40)
