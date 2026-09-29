from audio_helpers import *
import subprocess,sys
from bie.qa.audio_v2.bridge import prepare_release_evidence
from bie.qa.audio_v2.codec import decode,load_request,load_policy
from bie.qa.audio_v2.adapters import from_native_alignment
from bie.qa.release_v2.evaluator import ReleaseEvaluator
from bie.qa.release_v2.contracts import EvidenceBundle
from jsonschema import Draft202012Validator

class IntegrationTests(FixtureCase):
    def prepare(self,r=None,c=None):
        r=self.r if r is None else r;c=self.c if c is None else c
        return prepare_release_evidence(r,c,self.root,self.p,as_of=NOW,**options(r,self.p))
    def test_full_media_gate_not_run(self):self.assertEqual(self.prepare().envelope.status,'NOT_RUN')
    def test_evidence_is_unsigned(self):e=self.prepare().envelope;self.assertEqual((e.signer_key_id,e.signature),('UNSIGNED',''))
    def test_failed_audio_gate_fail(self):(self.root/self.r.clips[0].wav.path).write_bytes(b'bad');self.assertEqual(self.prepare().envelope.status,'FAIL')
    def test_report_hash(self):
        x=self.prepare();self.assertEqual(hashlib.sha256(x.report_bytes).hexdigest(),x.envelope.report.sha256);self.assertEqual(len(x.report_bytes),x.envelope.report.size)
    def test_existing_release_evaluator_blocks(self):
        x=self.prepare();f=self.root/x.envelope.report.path;f.parent.mkdir(parents=True);f.write_bytes(x.report_bytes)
        result=ReleaseEvaluator().evaluate(EvidenceBundle('2.0.0',self.c,(x.envelope,)),self.root,as_of=NOW)
        self.assertEqual(result.release_status,'BLOCKED');self.assertFalse(result.product_accepted)
    def test_candidate_binding_reject(self):
        with self.assertRaises(ContractError):self.prepare(c=replace(self.c,candidate_id='other'))
    def test_audio_must_be_in_candidate(self):
        r=self.timing(basis='reported')
        with self.assertRaises(ContractError):self.prepare(r)
    def test_bridge_does_not_write(self):self.prepare();self.assertFalse((self.root/'qa_audio_reports').exists())
    def test_schemas(self):
        for name,obj in [('request',self.r),('policy',self.p),('review',signed_reviews(self.r,self.p)[0])]:
            with self.subTest(schema=name):
                schema=json.loads((ROOT/f'docs/qa_section16/batch010/{name}.schema.json').read_bytes());Draft202012Validator.check_schema(schema);Draft202012Validator(schema).validate(json.loads(canonical_bytes(asdict(obj))))
    def cli(self,output=None):
        a=self.root/'request.json';b=self.root/'policy.json';a.write_bytes(canonical_bytes(asdict(self.r)));b.write_bytes(canonical_bytes(asdict(self.p)))
        cmd=[sys.executable,'-B','-m','bie.qa.audio_v2','--request',str(a),'--policy',str(b),'--artifact-root',str(self.root),'--as-of',str(NOW)]
        if output:cmd+=['--output',str(output)]
        return subprocess.run(cmd,cwd=ROOT,capture_output=True,timeout=10)
    def test_cli_review_only(self):r=self.cli();self.assertEqual(r.returncode,3,r.stderr);self.assertEqual(json.loads(r.stdout)['status'],'REVIEW_REQUIRED')
    def test_cli_exclusive_output(self):
        f=self.root/'exists.json';f.write_bytes(b'preserve');r=self.cli(f);self.assertEqual(r.returncode,4);self.assertEqual(f.read_bytes(),b'preserve')
    def test_cli_blocked_bytes(self):(self.root/self.r.clips[0].wav.path).write_bytes(b'bad');self.assertEqual(self.cli().returncode,2)

class NativeAdapterTests(FixtureCase):
    def native(self):
        t=decode(json.loads((self.root/self.r.clips[0].timing.path).read_bytes()),TimingReceipt)
        return dict(schema_version='bie.audio.word-timing/1',media_sha256=t.audio_sha256,sample_rate=t.sample_rate,provider_samples=t.samples,pause_samples=0,basis='ESPEAK_MARK_EVENTS_SAME_PCM',acoustic_alignment_verified=False,pronunciation_verified=False,product_accepted=False,words=[dict(index=w.index,spoken_start=w.start_char,spoken_end=w.end_char,spoken=w.text,start_sample=w.start_sample,end_sample=w.end_sample,source=[],end_basis='ENGINE_MARK_BOUNDARY') for w in t.words])
    def adapt(self,n=None):return from_native_alignment(self.native() if n is None else n,clip_id='clip',spoken_text=self.p.narrations[0].spoken_text,audio_sha256=self.r.clips[0].wav.sha256)
    def test_native_engine_stays_engine(self):self.assertEqual(self.adapt().basis,'engine_events')
    def test_native_fixture_stays_synthetic(self):n=self.native();n['basis']='NEURAL_CHARACTER_FIXTURE_SAME_PCM';self.assertEqual(self.adapt(n).basis,'synthetic')
    def test_native_phonetic_claim_rejected(self):
        n=self.native();n['acoustic_alignment_verified']=True
        with self.assertRaises(ContractError):self.adapt(n)
    def test_native_media_changed(self):
        n=self.native();n['media_sha256']='0'*64
        with self.assertRaises(ContractError):self.adapt(n)
    def test_native_text_changed(self):
        n=self.native();n['words'][0]['spoken']='Wrong'
        with self.assertRaises(ContractError):self.adapt(n)
    def test_native_pause_not_word_extension(self):
        n=self.native();n['provider_samples']=7999;n['pause_samples']=1
        with self.assertRaises(ContractError):self.adapt(n)
    def test_native_unknown_basis_rejected(self):
        n=self.native();n['basis']='CERTIFIED'
        with self.assertRaises(ContractError):self.adapt(n)
