import unittest
from bie.reasoning.temporal_section_readiness import *
class T(unittest.TestCase):
 def test_unit_block(self): self.assertEqual(temporal_section_state(TemporalReadiness(False,False,False,False,False)),"IMPLEMENTED_WITH_GAPS")
 def test_integration_block(self): self.assertEqual(temporal_section_state(TemporalReadiness(True,False,True,False,True)),"IMPLEMENTATION_SCOPE_BLOCKED")
 def test_not_accepted(self): self.assertEqual(temporal_section_state(TemporalReadiness(True,True,True,False,True)),"IMPLEMENTATION_SCOPE_COMPLETE_NOT_ACCEPTED")
 def test_candidate(self): self.assertEqual(temporal_section_state(TemporalReadiness(True,True,True,True,True)),"ACCEPTANCE_CANDIDATE")
