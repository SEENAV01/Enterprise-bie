"""H1-008 pure admission controls; these are NOT native execution evidence."""
from pathlib import Path
import json
import os
import sys
import unittest

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from bie.compiler import chromium_resource_worker as boundary
from bie.compiler.qa_common import CompilerQAError

NODE='/opt/nvm/versions/node/v22.16.0/bin/node'
PAINT=[NODE,'--disable-wasm-trap-handler','/engine/bie/compiler/qa_support/remotion_raster_capture.cjs','/work/capture-request.json']
ARGS=['about:blank','--no-sandbox','--remote-debugging-port=0','--headless=new',
      '--user-data-dir=/tmp/puppeteer_dev_chrome_profile-unit']
WORK=Path('/owned-project')
BROWSER='/usr/local/lib/bie-section18-chromium/chrome'
RENDER=[NODE,str(WORK/'node_modules/@remotion/cli/remotion-cli.js'),'render',str(WORK/'src/index.ts'),
        'Composition','/work/evidence/staged.mp4','--browser-executable='+BROWSER]

class ChromiumResourceAdmission(unittest.TestCase):
    def rejects(self,call,code):
        with self.assertRaisesRegex(CompilerQAError,'CHROMIUM_RESOURCE_'+code):call()
    def test_explicit_limits_remain_finite_and_node_default_unchanged(self):
        self.assertEqual(boundary.NODE_AS,8*1024**3)
        self.assertEqual(boundary.CHROME_AS,2*1024**4)
        self.assertEqual(boundary.PHYSICAL_MEMORY,2*1024**3)
        # Exact live WorkerPolicy comparison belongs to the supported native
        # lane; Windows must not fake fcntl or import a substitute worker.
    def test_pinned_paint_command_unchanged(self):
        self.assertEqual(boundary.approved_command(PAINT,WORK,BROWSER,'actual-paint'),PAINT)
    def test_only_genuine_render_cli_gains_explicit_wasm_flag(self):
        out=boundary.approved_command(RENDER,WORK,BROWSER,'renderer')
        self.assertEqual(out[:4],[NODE,'--disable-wasm-trap-handler',RENDER[1],'render'])
        self.assertIn('--browser-executable='+boundary.ENTRY,out)
        self.assertEqual(RENDER[1],str(WORK/'node_modules/@remotion/cli/remotion-cli.js'))
    def test_admission_does_not_mutate_input_or_environment(self):
        before=dict(os.environ);copy=list(RENDER)
        boundary.approved_command(RENDER,WORK,BROWSER,'renderer')
        self.assertEqual(copy,RENDER);self.assertEqual(before,dict(os.environ))
    def test_unrelated_node_command_rejected(self):
        self.rejects(lambda:boundary.approved_command([NODE,'-e','1+1'],WORK,BROWSER,'renderer'),'RENDER_COMMAND')
    def test_arbitrary_node_version_rejected(self):
        self.rejects(lambda:boundary.approved_command(['/usr/bin/node',*PAINT[1:]],WORK,BROWSER,'actual-paint'),'NODE_PIN')
    def test_generic_profile_kind_rejected(self):
        self.rejects(lambda:boundary.approved_command(PAINT,WORK,BROWSER,'generic'),'COMMAND_KIND')
    def test_missing_paint_flag_rejected(self):
        self.rejects(lambda:boundary.approved_command([PAINT[0],*PAINT[2:]],WORK,BROWSER,'actual-paint'),'PAINT_COMMAND')
    def test_paint_source_substitution_rejected(self):
        self.rejects(lambda:boundary.approved_command([*PAINT[:2],'/work/evil.cjs',PAINT[3]],WORK,BROWSER,'actual-paint'),'PAINT_COMMAND')
    def test_extra_paint_argument_rejected(self):
        self.rejects(lambda:boundary.approved_command([*PAINT,'--inspect'],WORK,BROWSER,'actual-paint'),'PAINT_COMMAND')
    def test_shell_and_nul_rejected(self):
        self.rejects(lambda:boundary.approved_command([NODE,'\0'],WORK,BROWSER,'renderer'),'COMMAND')
    def test_renderer_foreign_cli_rejected(self):
        self.rejects(lambda:boundary.approved_command([NODE,'/tmp/foreign.js',*RENDER[2:]],WORK,BROWSER,'renderer'),'RENDER_COMMAND')
    def test_renderer_browser_must_be_exact_pin_path(self):
        self.rejects(lambda:boundary.approved_command([*RENDER[:-1],'--browser-executable=/tmp/evil'],WORK,BROWSER,'renderer'),'RENDER_BROWSER')
    def test_renderer_missing_browser_rejected(self):
        self.rejects(lambda:boundary.approved_command(RENDER[:-1],WORK,BROWSER,'renderer'),'RENDER_BROWSER')
    def test_renderer_duplicate_browser_rejected(self):
        self.rejects(lambda:boundary.approved_command([*RENDER,RENDER[-1]],WORK,BROWSER,'renderer'),'RENDER_BROWSER')
    def test_renderer_additional_node_flags_rejected(self):
        self.rejects(lambda:boundary.approved_command([*RENDER,'--js-flags=--no-sandbox'],WORK,BROWSER,'renderer'),'RENDER_NODE_FLAGS')
    def test_pinned_browser_argument_set_accepted(self):
        args=sorted(boundary.FIXED_ARGS)+ARGS[3:]
        self.assertEqual(boundary.validate_browser_args(args),tuple(args))
    def test_generated_numeric_browser_arguments_accepted(self):
        self.assertEqual(boundary.validate_browser_args(ARGS+['--video-threads=128','--window-size=640,360','--force-device-scale-factor=1']),
            tuple(ARGS+['--video-threads=128','--window-size=640,360','--force-device-scale-factor=1']))
    def test_browser_arbitrary_url_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['https://example.invalid']),'ARG_NOT_PINNED')
    def test_browser_disable_v8_sandbox_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--js-flags=--no-sandbox']),'ARG_NOT_PINNED')
    def test_browser_single_process_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--single-process']),'ARG_NOT_PINNED')
    def test_browser_extension_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--load-extension=/work/evil']),'ARG_NOT_PINNED')
    def test_browser_foreign_profile_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS[:-1]+['--user-data-dir=/work/profile']),'ARG_NOT_PINNED')
    def test_browser_redirect_debug_address_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--remote-debugging-address=0.0.0.0']),'ARG_NOT_PINNED')
    def test_browser_duplicate_argument_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+[ARGS[0]]),'DUPLICATE_ARG')
    def test_browser_conflicting_headless_mode_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--headless=old']),'HEADLESS_ARG')
    def test_browser_conflicting_profile_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--user-data-dir=/tmp/puppeteer_dev_chrome_profile-second']),'PROFILE_ARG')
    def test_browser_thread_upper_boundary_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['--video-threads=129']),'ARG_NOT_PINNED')
    def test_browser_control_chars_rejected(self):
        self.rejects(lambda:boundary.validate_browser_args(ARGS+['\n--no-sandbox']),'ARGS')
    def test_safe_constants_roundtrip_without_secret_material(self):
        receipt=dict(node_limit=boundary.NODE_AS,browser_limit=boundary.CHROME_AS,memory=boundary.PHYSICAL_MEMORY,
                     browser_sha256=boundary.CHROME_SHA,entry=boundary.ENTRY)
        self.assertEqual(json.loads(json.dumps(receipt)),receipt)

if __name__=='__main__':unittest.main(verbosity=2)
