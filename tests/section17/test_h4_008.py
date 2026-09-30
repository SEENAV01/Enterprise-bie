import unittest
from bie.evaluation.benchmarks.models import digest
from bie.evaluation.benchmarks.browser.native import map_dist
from bie.evaluation.benchmarks.metrics import evaluate
from bie.evaluation.benchmarks.browser.document import prepare
from bie.evaluation.benchmarks.browser.contracts import candidate as validate_candidate
from h4_support import reference,candidate,context,assert_error,GAME
class H4008(unittest.TestCase):
 def test_existing_metric_api_executes_browser(self):
  r=reference();c=candidate();x=evaluate(r['metric_id'],r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),execution_context=context())
  self.assertEqual(x['outcome'],'PASS');self.assertEqual(x['metric_profile'],'game-runtime-behavior-1')
 def test_injected_receipt_rejected(self):
  r=reference();c=candidate();assert_error(self,lambda:evaluate(r['metric_id'],r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c),execution_context=context(),source_artifacts={'passed':True}),'BROWSER_INJECTED_EVIDENCE_REJECTED')
 def test_reference_pin_required(self):
  r=reference();c=candidate();assert_error(self,lambda:evaluate(r['metric_id'],r,c,expected_reference_sha256='0'*64,expected_candidate_sha256=digest(c),execution_context=context()),'REFERENCE_SNAPSHOT_MISMATCH')
 def test_context_required(self):
  r=reference();c=candidate();assert_error(self,lambda:evaluate(r['metric_id'],r,c,expected_reference_sha256=digest(r),expected_candidate_sha256=digest(c)),'TRUSTED_BROWSER_CONTEXT_REQUIRED')
 def test_native_layout_missing_required_assets(self):assert_error(self,lambda:map_dist([],expected_manifest_sha256=digest([])),'GAME_DIST_REQUIRED_FILES_MISSING')
 def test_native_layout_pin(self):assert_error(self,lambda:map_dist([],expected_manifest_sha256='0'*64),'GAME_DIST_MANIFEST_PIN_MISMATCH')
 def test_classic_document_keeps_script_digest(self):
  c=candidate();assets={p.name:p.read_bytes() for p in GAME.iterdir()};_,scripts,transport=prepare(c,assets)
  self.assertEqual(len(scripts),1);self.assertEqual(scripts[0]['path'],'game.js');self.assertFalse(transport['module_boot_verified'])
 def test_es_module_not_fake_executed(self):
  c=candidate();assets={p.name:p.read_bytes() for p in GAME.iterdir()};assets['index.html']=assets['index.html'].replace(b'<script src=',b'<script type="module" src=')
  assert_error(self,lambda:prepare(c,assets),'BROWSER_ES_MODULE_BOOT_UNSUPPORTED')
 def test_external_stylesheet_not_fetched(self):
  c=candidate();assets={p.name:p.read_bytes() for p in GAME.iterdir()};assets['index.html']=assets['index.html'].replace(b'href="styles.css"',b'href="https://example.com/a.css"')
  assert_error(self,lambda:prepare(c,assets),'BROWSER_EXTERNAL_ASSET_UNSUPPORTED')
