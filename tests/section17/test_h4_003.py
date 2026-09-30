import unittest,tempfile,shutil
from dataclasses import replace
from pathlib import Path
from bie.evaluation.benchmarks.browser.service import execute,binary_hash,verify_receipt
from bie.evaluation.benchmarks.browser.contracts import BrowserLimits
from h4_support import GAME,receipt,reference,candidate,context,assert_error
class H4003(unittest.TestCase):
 def test_actual_chromium_runs(self):
  x=receipt();self.assertEqual(x['status'],'COLLECTED');self.assertTrue(x['observed']['browser_version'])
 def test_two_fresh_contexts(self):self.assertEqual([r['fresh_context_index'] for r in receipt()['observed']['runs']],[0,1])
 def test_tool_pin_failure_is_blocked(self):
  x=execute(reference(),candidate(),replace(context(),chromium_sha256='0'*64));self.assertEqual(x['error_code'],'BROWSER_TOOL_PIN_MISMATCH')
 def test_receipt_tamper_rejected(self):
  x=receipt();x['status']='PASS';assert_error(self,lambda:verify_receipt(x),'BROWSER_RECEIPT_INTEGRITY')
 def test_network_not_claimed_sandbox(self):self.assertFalse(receipt()['observed']['hostile_code_sandbox_verified'])
 def test_external_request_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'g';shutil.copytree(GAME,root)
   with (root/'game.js').open('a') as f:f.write("\nfetch('https://example.com/blocked').catch(()=>{});\n")
   x=execute(reference(),candidate(root),context(root));self.assertEqual(x['status'],'COLLECTED')
   self.assertTrue(x['observed']['runs'][0]['events']['blocked_requests'])
 def test_runtime_exception_captured(self):
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'g';shutil.copytree(GAME,root)
   with (root/'game.js').open('a') as f:f.write("\nsetTimeout(()=>{throw new Error('injected-runtime-fault')},0);\n")
   x=execute(reference(),candidate(root),context(root));self.assertEqual(x['status'],'COLLECTED');self.assertTrue(x['observed']['runs'][0]['events']['page_errors'])
 def test_hanging_script_deadline(self):
  limits=replace(BrowserLimits(),total_timeout_seconds=2)
  with tempfile.TemporaryDirectory() as t:
   root=Path(t)/'g';shutil.copytree(GAME,root);(root/'game.js').write_text('while(true){}')
   x=execute(reference(limits),candidate(root),context(root,limits));self.assertEqual(x['status'],'BLOCKED');self.assertEqual(x['error_code'],'AV_DEADLINE')
