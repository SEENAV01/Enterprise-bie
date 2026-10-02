"""Real pinned Remotion bundling under the unchanged read-only namespace policy.

Default caching is a defect reproduction, not a mocked renderer. The positive
control uses the supported option used by the active producer. No cache directory
or dependency is made writable; no compiler runner or proof is substituted.
"""
from pathlib import Path
import json
import os
import shutil
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bie.compiler.linux_worker import run_isolated,WorkerPolicy
from bie.compiler.installed_toolchain import collect_installed_toolchain,require_same_toolchain


class NativeBundleCache(unittest.TestCase):
    def setUp(self):
        if sys.platform!='linux':raise RuntimeError('native Linux required; no bundler fallback')
        prepared=os.environ.get('BIE_SECTION18_RENDER_PROJECT')
        if not prepared:raise RuntimeError('prepared pinned render project required')
        self.temp=tempfile.TemporaryDirectory(prefix='bie-bundle-cache-regression-')
        self.root=Path(self.temp.name);self.project=self.root/'project'
        shutil.copytree(Path(prepared),self.project,symlinks=True,
                        ignore=shutil.ignore_patterns('out','render-evidence','validation-runs'))
        self.node=shutil.which('node');self.assertIsNotNone(self.node)
        self.browser='/opt/bie-game-chromium/chrome'
        self.before=collect_installed_toolchain(self.project,node=self.node,browser=self.browser)
        self.assertEqual(json.loads((self.project/'node_modules/@remotion/bundler/package.json').read_text())['version'],'4.0.506')
        self.assertFalse((self.project/'node_modules/.cache').exists())
        (self.project/'capture-output').mkdir()

    def tearDown(self):self.temp.cleanup()

    def bundle(self,cache_option):
        source="""'use strict';
const {bundle}=require('@remotion/bundler');
bundle({entryPoint:'/work/src/index.ts',outDir:'/work/capture-output/bundle',publicDir:'/work/public',OPTION})
 .then(output=>console.log('REAL_BUNDLE_READY:'+output))
 .catch(error=>{console.error(String(error));process.exitCode=2;});
""".replace('OPTION',cache_option)
        script=self.project/'cache-control.cjs';script.write_text(source)
        process,kernel=run_isolated([self.node,str(script)],workspace=self.project,
            writable=['capture-output'],policy=WorkerPolicy(),timeout_s=120,
            max_output_bytes=1024*1024)
        require_same_toolchain(self.before,collect_installed_toolchain(self.project,node=self.node,browser=self.browser))
        self.assertTrue(kernel['kernel_enforced'])
        self.assertFalse((self.project/'node_modules/.cache').exists())
        return process

    def test_default_cache_reproduces_readonly_dependency_failure(self):
        process=self.bundle('')
        self.assertFalse(process.process.passed)
        self.assertNotIn('REAL_BUNDLE_READY:',process.process.stdout)
        self.assertIn('node_modules/.cache/webpack',process.process.stderr)

    def test_disabled_cache_bundles_without_dependency_mutation(self):
        producer=(ROOT/'bie/compiler/qa_support/remotion_raster_capture.cjs').read_text()
        self.assertIn('enableCaching:false',producer)
        process=self.bundle('enableCaching:false')
        self.assertTrue(process.process.passed,process.process.stderr)
        self.assertIn('REAL_BUNDLE_READY:/work/capture-output/bundle',process.process.stdout)
        self.assertTrue((self.project/'capture-output/bundle/index.html').is_file())


if __name__=='__main__':unittest.main(verbosity=2)
