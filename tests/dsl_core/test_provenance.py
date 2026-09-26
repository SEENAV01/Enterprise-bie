import unittest
from dataclasses import replace
from bie.game_engine.errors import GameContractError
from bie.game_engine.provenance import *
class T(unittest.TestCase):
 def ref(self,role='source',aid='a'):return EvidenceRef(aid,'p:1','0'*64,role)
 def test_valid(self):ProvenanceBundle((self.ref('source','s'),self.ref('reasoning','r'))).validate()
 def test_missing_required(self):
  with self.assertRaises(GameContractError):ProvenanceBundle((self.ref('source','s'),)).validate()
 def test_hash_required(self):
  with self.assertRaises(GameContractError):EvidenceRef('a','p','x','source').validate()
 def test_role(self):
  with self.assertRaises(GameContractError):self.ref('x').validate()
 def test_duplicate(self):
  r=self.ref('source','s')
  with self.assertRaises(GameContractError):ProvenanceBundle((r,r,self.ref('reasoning','r'))).validate()
