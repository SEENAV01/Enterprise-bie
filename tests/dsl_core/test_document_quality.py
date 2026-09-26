import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.fixtures import sample_document
from bie.game_engine.document import *
from bie.game_engine.quality_intent import *
from bie.game_engine.visual import VisualExperienceContract
class T(unittest.TestCase):
 def test_valid(self):sample_document().validate()
 def test_product_acceptance_forbidden(self):
  with self.assertRaises(GameContractError):replace(sample_document(),product_accepted=True).validate()
 def test_quality_weakened(self):
  with self.assertRaises(GameContractError):ExperienceQualityIntent(anti_slide_default=False).validate()
 def test_slide_only_forbidden(self):
  d=sample_document();c=replace(d.experiences[0].levels[0].challenges[0],mode=ExperienceMode.REFERENCE);l=replace(d.experiences[0].levels[0],challenges=(c,));e=replace(d.experiences[0],levels=(l,));
  with self.assertRaises(GameContractError):replace(d,experiences=(e,)).validate()
 def test_dynamic_requires_motion(self):
  d=sample_document();l=d.experiences[0].levels[0];l=replace(l,visual=replace(l.visual,motion=()));e=replace(d.experiences[0],levels=(l,));
  with self.assertRaises(GameContractError):replace(d,experiences=(e,)).validate()
 def test_duplicate_experience(self):
  d=sample_document();
  with self.assertRaises(GameContractError):replace(d,experiences=(d.experiences[0],d.experiences[0])).validate()
 def test_fingerprint_deterministic(self):self.assertEqual(sample_document().fingerprint(),sample_document().fingerprint())
