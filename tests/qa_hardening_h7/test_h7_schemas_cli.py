from h7_helpers import *
import subprocess,jsonschema

class SchemasCLI(Temp):
    def test_seven_structural_schemas_and_negative_controls(self):
        src=self.root/'dep';p,r=dependency_fixture(src)
        prog=make_program(self.root/'tool.py','pass')
        pp=NativeWorkerProfile(p.file_rows,'a'*64,'b'*64)
        data={'program':asdict(prog),'dependency_policy':asdict(p),'dependency_review':r,
              'workload':{'expected_jobs':['x'],'records':[dict(job_id='x',execution_id='e',submitted_ns=0,started_ns=1,finished_ns=2,exit_code=0,output_verified=True)]},
              'aggregate_limits':asdict(AggregateLimits()),'native_profile':asdict(pp),
              'report':local_report('BIE-QA-HARD-030',Binding('r','a'*40,'b'*64,'c'*64),{})}
        base=Path(__file__).resolve().parents[2]/'hardening/section16_h7/schemas'
        for name,value in data.items():
            with self.subTest(schema=name):
                schema=json.loads((base/(name+'.schema.json')).read_text());jsonschema.Draft202012Validator.check_schema(schema)
                value=json.loads(json.dumps(value));jsonschema.validate(value,schema)
                with self.assertRaises(jsonschema.ValidationError):jsonschema.validate({**value,'undeclared':True},schema)
    def test_readonly_cli(self):
        (self.root/'input').mkdir();(self.root/'input/a').write_text('source');before=inventory(self.root/'input')
        p=subprocess.run([sys.executable,'-B','-m','bie.qa.operational_quality_v2',str(self.root/'input')],capture_output=True,text=True,env={**os.environ,'OAI_IS_JUPYTER_KERNEL':'0'})
        self.assertEqual(p.returncode,3,p.stderr);self.assertEqual(json.loads(p.stdout)['status'],'REVIEW_REQUIRED');self.assertEqual(before,inventory(self.root/'input'))
    def test_cli_missing_directory(self):
        p=subprocess.run([sys.executable,'-B','-m','bie.qa.operational_quality_v2',str(self.root/'missing')],capture_output=True,text=True,env={**os.environ,'OAI_IS_JUPYTER_KERNEL':'0'})
        self.assertEqual(p.returncode,4);self.assertEqual(json.loads(p.stderr)['status'],'BLOCKED')
    def test_native_stage_needs_paired_profile(self):
        prog=make_program(self.root/'x.py','pass')
        self.error('H7_NATIVE_STAGE_PAIR',Stage,'x','compile',prog,('x',),native_checkout=str(self.root))
    def test_native_stage_script_confined_to_approved_engine(self):
        prog=make_program(self.root/'x.py','pass');pp=NativeWorkerProfile(({'path':'x','sha256':'a'*64,'bytes':1},),'a'*64,'b'*64)
        self.error('H7_NATIVE_SCRIPT_OUTSIDE_ENGINE',Stage,'x','compile',prog,('x',),native_profile=pp,native_checkout='/not-here')
    def test_unknown_stage_role(self):
        self.error('H7_STAGE_ROLE',Stage,'x','forge-approval',make_program(self.root/'x.py','pass'),('x',))
    def test_false_native_proof(self):
        pp=NativeWorkerProfile(({'path':'x','sha256':'a'*64,'bytes':1},),'a'*64,'b'*64)
        self.error('H7_NATIVE_PROOF_SCHEMA',validate_kernel_proof,{'status':'PASS'},pp)
