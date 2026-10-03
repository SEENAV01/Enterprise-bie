"""Actual Linux Remotion -> native decode -> persisted operator media.

Canonical guarded renderer, no injected runner/decoder/paint witness. The source
is explicitly a tiny synthetic technical scene, not learning or book acceptance.
"""
from pathlib import Path
import os
import hashlib
import json
import sys
import unittest
from dataclasses import asdict,replace

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base
from apps.operator.previews import Previews
from bie.compiler.hardened_scene_compile import require_h3_workspace
from bie.compiler.render_contracts import RenderRequest
from bie.compiler.remotion_composition_discovery import CompositionDescriptor
from bie.compiler.full_render import full_render
from bie.compiler.qa_common import digest
from bie.compiler.linux_worker import WorkerPolicy
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
        # The default /opt copy used by GAME is deliberately absent inside the
        # compiler chroot. CI provisions that exact browser under the existing
        # read-only /usr mount; no namespace/mount/resource policy expansion.
        browser=os.environ.get('BIE_SECTION18_RENDER_BROWSER')
        if not browser:raise RuntimeError('explicit sandbox-visible browser required; no auto-download')
        binary=Path(browser)
        if binary.is_symlink() or not binary.is_file() or not binary.is_relative_to('/usr'):
            raise RuntimeError('sandbox-visible browser must be a regular /usr tool')
        with binary.open('rb') as stream:
            if stream.read(4)!=b'\x7fELF':raise RuntimeError('native browser ELF required')
        request=RenderRequest(str(cls.project),'src/index.ts',comp,'out/preview.mp4',source.scene_fingerprint,
                              'operator18-native-preview',browser_executable=str(binary),timeout_s=120)
        cls.receipt=full_render(request)
        # Keep the real producer's exact invocation even on a failed render.
        # Export only execution/policy metadata, never raw stdout/stderr or scene
        # content. This record cannot manufacture an ActualPaintWitness or PASS.
        command_path=cls.project/cls.receipt.evidence_directory/'actual-paint/PROCESS.json'
        if command_path.is_file():
            if command_path.is_symlink() or not command_path.resolve().is_relative_to(cls.project.resolve()):
                raise AssertionError('actual-paint command evidence path rejected')
            if not 0<command_path.stat().st_size<=8*1024**2:
                raise AssertionError('actual-paint command evidence size rejected')
            raw=command_path.read_bytes()
            process_record=json.loads(raw)
            command=process_record['command'];kernel=process_record['kernel_policy']
            if (type(command) is not list or len(command)!=4 or type(command[0]) is not str or
                not Path(command[0]).is_absolute() or Path(command[0]).name!='node' or
                command[1:]!=['--disable-wasm-trap-handler',
                    '/engine/bie/compiler/qa_support/remotion_raster_capture.cjs','/work/capture-request.json']):
                raise AssertionError('actual-paint command scope rejected')
            if (kernel['resource_limits']!=asdict(WorkerPolicy()) or kernel['kernel_enforced'] is not True or
                kernel['capabilities_dropped'] is not True or kernel['no_new_privileges'] is not True or
                kernel['private_network']!='LOOPBACK_ONLY_NO_HOST_ROUTE'):
                raise AssertionError('actual-paint unchanged kernel policy required')
            process=process_record['process']
            cls.actual_paint_command_receipt=dict(schema='bie.section18.actual-paint-command/1',
                producer_receipt_sha256=hashlib.sha256(raw).hexdigest(),command=command,kernel_policy=kernel,
                process_started=process['started'],process_outcome=process['outcome'],
                process_passed=process['process']['passed'],actual_paint_pass_claimed=False,
                stdout_stderr_or_scene_content_exported=False,synthetic_test=True,product_accepted=False)
        if not cls.receipt.passed:
            # Retain exact native typecheck evidence from the canonical producer.
            # This diagnostic reads the synthetic CI workspace only and does not
            # replace the producer, inject a witness, or relax source coverage.
            path=cls.project/cls.receipt.evidence_directory/'actual-paint/typecheck/TYPECHECK.json'
            cls.failure_diagnostic=dict(failure_code=cls.receipt.failure_code,
                                        errors=list(cls.receipt.errors),synthetic_source=True)
            if path.is_file():
                raw=path.read_bytes()
                if len(raw)<=8*1024**2:
                    report=json.loads(raw);gate=report['receipt']
                    cls.failure_diagnostic.update(typecheck_status=gate['status'],
                        listed_sources=[line.rsplit('/',1)[-1] for line in report['executions'][0]['process']['process']['stdout'].splitlines()
                                        if '/node_modules/' not in line],
                        processes=[dict(outcome=e['process']['outcome'],
                                        started=e['process']['started'],
                                        passed=e['process']['process']['passed']) for e in report['executions']])
            raise AssertionError('native renderer failed closed: '+str(cls.receipt.failure_code)+': '+str(cls.receipt.errors))
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
        self.assertTrue(self.actual_paint_command_receipt['process_started'])
        self.assertTrue(self.actual_paint_command_receipt['process_passed'])
        self.assertEqual(self.actual_paint_command_receipt['kernel_policy']['resource_limits']['address_space_bytes'],8589934592)
        typecheck=json.loads((self.project/self.receipt.evidence_directory/
                              'actual-paint/typecheck/TYPECHECK.json').read_text())
        self.assertEqual(typecheck['receipt']['status'],'PASS')
        coverage=typecheck['executions'][0]['process']['process']['stdout']
        self.assertIn('/work/qa-paint-helper.js',coverage)
        self.assertIn('/work/qa-capture-entry.tsx',coverage)
        self.assertNotIn('qa-paint-helper.d.ts',coverage)

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
