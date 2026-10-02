"""Actual Linux Remotion -> native decode -> persisted operator media.

Canonical guarded renderer, no injected runner/decoder/paint witness. The source
is explicitly a tiny synthetic technical scene, not learning or book acceptance.
"""
from pathlib import Path
import os
import sys
import unittest
from dataclasses import replace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base
from apps.operator.previews import Previews
from bie.compiler.hardened_scene_compile import require_h3_workspace
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from bie.compiler.qa_common import digest
from bie.qa.video_v2.models import VideoPolicy


class NativePreviewRender(Base):
    @classmethod
    def setUpClass(cls):
        if sys.platform!='linux':raise RuntimeError('native Linux required; no renderer fallback')
        raw=os.environ.get('BIE_SECTION18_RENDER_PROJECT')
        if not raw:raise RuntimeError('explicit prepared native render project required')
        cls.project=Path(raw).absolute()
        source=require_h3_workspace(cls.project)
        comp=CompositionDescriptor('BieQA'+digest('section18-native-preview')[:16],640,360,12,6)
        request=RenderRequest(str(cls.project),'src/index.ts',comp,'out/preview.mp4',source.scene_fingerprint,
                              'operator18-native-preview',browser_executable='/opt/bie-game-chromium/chrome',timeout_s=120)
        cls.receipt=full_render(request)
        if not cls.receipt.passed:raise AssertionError('native renderer failed closed: '+str(cls.receipt.failure_code)+': '+str(cls.receipt.errors))
        cls.data=(cls.project/cls.receipt.output_path).read_bytes()
        cls.policy=VideoPolicy(comp.composition_id,cls.receipt.input_sha256,640,360,12,1,6)

    def setUp(self):
        super().setUp();self.run=self.make_run();self.preview=Previews(self.service)
        self.source_hash=self.service.status(self.p,self.run)['source_hash']

    def publish(self,receipt=None):
        return self.preview.publish_render(self.p,self.run,self.data,self.receipt if receipt is None else receipt,
                                           self.policy,source_hash=self.source_hash)

    def test_actual_renderer_paint_and_full_media_receipt(self):
        self.assertEqual(self.receipt.execution_kind,'LOCAL_REMOTION_CLI')
        self.assertTrue(self.receipt.process_started);self.assertFalse(self.receipt.accepted)
        self.assertEqual(self.receipt.media.decoded_frames,6)
        self.assertTrue((self.project/self.receipt.evidence_directory/'actual-paint-witness.json').is_file())
        self.assertTrue((self.project/self.receipt.evidence_directory/'isolation.json').is_file())

    def test_actual_native_decode_cas_binding_and_range_preview(self):
        view=self.publish();self.assertEqual(view['status'],'AVAILABLE')
        self.assertFalse(view['info']['release_authorized']);self.assertFalse(view['product_accepted'])
        raw,status,headers=self.preview.media(self.p,self.run,'bytes=0-31')
        self.assertEqual((status,raw),(206,self.data[:32]))
        self.assertEqual(headers['Content-Range'],'bytes 0-31/'+str(len(self.data)))
        self.assertEqual(Previews(self.service).get(self.p,self.run,'render')['artifact_id'],view['artifact_id'])

    def test_altered_actual_receipt_never_published(self):
        self.error(lambda:self.publish(replace(self.receipt,artifact_sha256='0'*64)),'render_receipt_invalid')
        self.assertEqual(self.preview.get(self.p,self.run,'render')['status'],'NOT_RUN')


if __name__=='__main__':unittest.main(verbosity=2)
