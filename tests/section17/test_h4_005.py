import unittest,base64,hashlib
from h4_support import receipt
class H4005(unittest.TestCase):
 def setUp(self):self.run=receipt()['observed']['runs'][0];self.q=self.run['steps'][0]['observations']['#question']
 def test_rendered_rectangle(self):self.assertGreater(self.q['bounds']['width'],0);self.assertGreater(self.q['bounds']['height'],0)
 def test_visible_observed(self):self.assertTrue(self.q['visible'])
 def test_viewport_observed(self):self.assertTrue(self.q['in_viewport'])
 def test_actual_text_contrast(self):self.assertGreater(self.q['contrast_at_least'],4.5)
 def test_actual_button_name(self):self.assertTrue(self.run['steps'][0]['observations']['#right']['has_accessible_name'])
 def test_feedback_live_region(self):self.assertEqual(self.run['steps'][2]['observations']['#feedback']['aria_live'],'polite')
 def test_screenshot_png_bytes(self):self.assertTrue(base64.b64decode(self.run['screenshot']['png_base64']).startswith(b'\x89PNG'))
 def test_screenshot_hash(self):self.assertEqual(hashlib.sha256(base64.b64decode(self.run['screenshot']['png_base64'])).hexdigest(),self.run['screenshot']['sha256'])
 def test_scope_not_full_accessibility(self):self.assertIn('NOT_COMPLETE_ACCESSIBILITY',self.q['observation_scope'])

 def test_observer_is_isolated_world(self):self.assertEqual(self.q['observer_world'],'ISOLATED_CDP')
 def test_candidate_style_api_spoof_does_not_change_observer(self):
  import tempfile,shutil
  from pathlib import Path
  from h4_support import GAME,context,candidate,reference
  from bie.evaluation.benchmarks.browser.service import execute
  with tempfile.TemporaryDirectory() as temp:
   root=Path(temp)/'g';shutil.copytree(GAME,root)
   with (root/'game.js').open('a') as out:out.write("\nwindow.getComputedStyle = () => { throw new Error('candidate replaced style API'); };\n")
   r=execute(reference(),candidate(root),context(root))
   self.assertEqual(r['status'],'COLLECTED')
   self.assertGreater(r['observed']['runs'][0]['steps'][0]['observations']['#question']['contrast_at_least'],4.5)
