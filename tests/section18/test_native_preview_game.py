"""Required Linux native game build/browser -> persisted operator preview.

Synthetic source/game content, actual canonical compiler/worker/browser. No
educational quality, real-book flow, learning improvement or release claim.
"""
from pathlib import Path
import os
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Path(__file__).parent))
from test_batch001 import Base
from apps.operator.previews import Previews
from bie.game_engine.build_runtime_engine.fixtures import build_inputs
from bie.game_engine.build_runtime_engine.pipeline import build_runtime_package
from bie.game_engine.compiler_engine.pipeline import compile_game


class NativePreviewGame(Base):
    @classmethod
    def setUpClass(cls):
        if sys.platform!='linux':raise RuntimeError('supported native Linux required; no fixture fallback')
        if os.geteuid()!=0:raise RuntimeError('approved disposable CI supervisor required; browser drops to canonical non-root UID')
        cls.workspace=tempfile.TemporaryDirectory(prefix='bie-app18-native-game-')
        cls.ctx,assets=build_inputs()
        cls.built=build_runtime_package(cls.ctx,assets,Path(cls.workspace.name))
        cls.bundle=compile_game(cls.ctx)
        dist=Path(cls.workspace.name)/'dist'
        cls.files={a.path:(dist/a.path).read_bytes() for a in cls.built.manifest.artifacts}
        cls.files['build-manifest.json']=(dist/'build-manifest.json').read_bytes()

    @classmethod
    def tearDownClass(cls):cls.workspace.cleanup()

    def setUp(self):
        super().setUp();self.run=self.make_run()
        self.source_hash=self.service.status(self.p,self.run)['source_hash']
        self.preview=Previews(self.service)

    def publish(self,files=None):
        return self.preview.publish_game(self.p,self.run,self.ctx,self.bundle,self.built.manifest,
            self.files if files is None else files,source_hash=self.source_hash,evidence_origin='SYNTHETIC_TEST')

    def test_actual_native_build_browser_and_replay_receipts(self):
        self.assertEqual(len(self.built.receipts),5)
        self.assertTrue(self.built.browser.studio_grade)
        self.assertTrue(self.built.browser.sandbox_no_new_privs)
        self.assertTrue(self.built.browser.renderer_seccomp)
        self.assertGreater(self.built.browser.sandbox_uid,0)
        self.assertEqual(self.built.browser.external_requests,())
        self.assertTrue(self.built.replay.success);self.assertTrue(self.built.replay.identical_second_run)
        self.assertFalse(self.built.product_accepted)

    def test_actual_package_bound_to_cas_and_scoped_preview_resources(self):
        view=self.publish();self.assertEqual(view['status'],'AVAILABLE')
        self.assertEqual(view['origin'],'SYNTHETIC_TEST')
        self.assertFalse(view['info']['release_authorized'])
        grant=self.preview.grant(self.p,self.run,self.token)
        ticket=grant['preview_path'].split('/')[2]
        data,media=self.preview.game_file(ticket,'runtime/entry.js')
        self.assertEqual(data,self.files['runtime/entry.js']);self.assertEqual(media,'text/javascript')
        self.assertEqual(Previews(self.service).get(self.p,self.run,'game')['artifact_id'],view['artifact_id'])

    def test_corrupted_actual_native_package_never_published(self):
        files=dict(self.files);files['runtime/entry.js']+=b'\n// altered after native build\n'
        self.error(lambda:self.publish(files),'game_package_invalid')
        self.assertEqual(self.preview.get(self.p,self.run,'game')['status'],'NOT_RUN')


if __name__=='__main__':unittest.main(verbosity=2)
