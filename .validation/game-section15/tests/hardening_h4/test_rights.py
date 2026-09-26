import unittest,json
from dataclasses import replace
from tests.hardening_h4.support import *
from bie.game_engine.errors import GameContractError
class RightsTests(unittest.TestCase):
 def test_asset_descriptor_carries_lineage(self):
  a=context().assets['audio:narration'];self.assertEqual(a.rights_ref,'rights:audio');self.assertEqual(a.license_id,'CC-BY-4.0');self.assertEqual(a.source_ref,'source:book')
 def test_context_requires_rights_for_asset(self):
  c=context();bad=replace(c,experience_profile=replace(profile(),rights=()))
  self.assertRaises(Exception,bad.validate)
 def test_rights_file_materialized(self):
  td,ws=build()
  try:
   p=ws.root/'dist/runtime/rights-attribution.json';self.assertTrue(p.is_file());d=json.loads(p.read_text());self.assertEqual(d['records'][0]['license_id'],'CC-BY-4.0')
  finally:td.cleanup()
 def test_dom_has_attribution(self):
  from bie.game_engine.compiler_engine.react_runtime import compile_react_runtime
  self.assertIn('data-rights-attribution',compile_react_runtime(context()).content)
 def test_duplicate_rights_rejected(self):
  r=profile().rights[0];self.assertRaises(GameContractError,replace(profile(),rights=(r,r)).validate)
