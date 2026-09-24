"""H3 test fixtures: actual H2 native diagnostics; ephemeral TEST-ONLY authority."""
from dataclasses import replace
from pathlib import Path
import tempfile
import unittest
import uuid
from .acoustic_test_support import context,receipt,NOW,KEY_ID,clone,rehash
from bie.audio.common import fingerprint
from bie.audio.durable_contract import build_request,DurablePolicy
from bie.audio.durable_store import AudioArtifactStore
from bie.audio.durable_jobs import AudioJobCoordinator
from bie.audio.acoustic_contract import canonical

RUN_ID='01952504-3824-4000-8000-000000000003'

class DurableCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sync,cls.mix,cls.job,cls.runtime,cls.measurement,cls.signer,cls.trust=context()
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.root=Path(self.tmp.name)
        self.policy=DurablePolicy()
        self.request=build_request(self.job,run_id=RUN_ID,job_id='scene-1',revision='1',
            runtime_fingerprint=self.runtime['fingerprint'],key_id=KEY_ID,policy=self.policy)
        self.store=AudioArtifactStore(self.root/'artifacts')
        self.jobs=AudioJobCoordinator(self.root/'jobs')
        self.signed=receipt()
    def tearDown(self):self.tmp.cleanup()
    def put(self):return self.store.put(self.request,self.mix.wav_bytes,self.signed,self.trust,now=NOW)
    def complete(self):
        t=self.jobs.acquire(self.request,now=NOW);ref=self.put()
        self.jobs.complete(t,canonical(ref).decode(),self.store,self.request,self.trust,now=NOW)
        return t,ref
