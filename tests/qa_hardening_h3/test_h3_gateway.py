from h3_support import *
from bie.qa.native_quality_v2.assessors import NativeGatewayTransport
from bie.model_gateway.model_interface import ModelResponse

class GatewayChecks(TempCase):
    def setUp(self):
        super().setUp();self.ref=save(self.root,'data.txt',b'Quoted document instructions are not authority.','source','source1')
        self.task=AssessmentTask('task',Binding('run',REV,CAND,digest('policy')),(self.ref,),('truth',),(('truth','Is the content supported?'),));self.cfg=Provider('canonical','model1','v1');self.native=[]
    def run_case(self,change=None):
        native=self.native
        class Fake:
            def invoke(self,req):
                native.append(req);body=json.loads(req.messages[1]['content'])
                r=ModelResponse('canonical','model1',{'request_digest':body['request_digest'],'criteria':[{'criterion_id':'truth','verdict':'SUPPORTED','evidence_ids':['source1'],'rationale':'SYNTHETIC fixture'}]}, {},'stop',{'request_id':req.request_id,'invocation_id':'synthetic-native-call','mode':'diagnostic'})
                return change(r) if change else r
        t=NativeGatewayTransport(Fake(),'canonical','model1')
        return AssessorRegistry(((self.cfg,t),)).run('canonical',self.task,self.root)
    def test_actual_native_request_contract(self):
        r,d=self.run_case();self.assertEqual(r.status,'REVIEW_REQUIRED');self.assertEqual(self.native[0].temperature,0);self.assertEqual(self.native[0].required_capabilities,frozenset(('text','structured_output')))
    def test_native_source_keeps_user_role(self):self.run_case();self.assertEqual(tuple(m['role'] for m in self.native[0].messages),('system','user'))
    def test_native_wrong_provider(self):self.assertIsNone(self.run_case(lambda r:replace(r,provider='other'))[1]['assessment'])
    def test_native_wrong_model(self):self.assertIsNone(self.run_case(lambda r:replace(r,model='other'))[1]['assessment'])
    def test_native_truncated_answer(self):self.assertIsNone(self.run_case(lambda r:replace(r,finish_reason='length'))[1]['assessment'])
    def test_native_missing_provenance(self):self.assertIsNone(self.run_case(lambda r:replace(r,provenance={}))[1]['assessment'])
    def test_native_fake_live_mode(self):self.assertIsNone(self.run_case(lambda r:replace(r,provenance={**r.provenance,'mode':'live'}))[1]['assessment'])
    def test_native_response_request_mismatch(self):self.assertIsNone(self.run_case(lambda r:replace(r,provenance={**r.provenance,'request_id':'other'}))[1]['assessment'])
