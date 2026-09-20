import unittest
from bie.scene_ir.unified_scene_ir_contract import *
from bie.scene_ir.dsl_realbook_harness import *
class T(unittest.TestCase):
 def f(self):return RealBookSceneIRFixture("p","physics","REAL_BOOK","book://x","user_supplied","a"*64,True,("text","equation"),("reveal",))
 def d(self):
  a=UnifiedElement("t","text",{"text":"C"},("s",),("r",));b=UnifiedElement("e","equation",{"expression":"F"},("s",),("r",));tr=UnifiedTrack("x","e","reveal",0,10,{},("s",),("r",));return UnifiedSceneIRDocument("s","1.0.0","T",10,(a,b),(tr,),("s",),("r",))
 def test_pass(self):self.assertEqual(evaluate_realbook_sceneir(self.f(),self.d()).status,"PASS")
 def test_hash(self):
  with self.assertRaises(ValueError):RealBookSceneIRFixture("x","p","REAL_BOOK","b","r","bad",True,("text",),())
 def test_kind(self):
  with self.assertRaises(ValueError):RealBookSceneIRFixture("x","p","SYNTHETIC","b","r","a"*64,True,("text",),())
 def test_independent(self):
  with self.assertRaises(ValueError):RealBookSceneIRFixture("x","p","REAL_BOOK","b","r","a"*64,False,("text",),())
 def test_fail(self):self.assertEqual(evaluate_realbook_sceneir(RealBookSceneIRFixture("x","p","REAL_BOOK","b","r","a"*64,True,("map",),()),self.d()).status,"FAIL")
 def test_not_accepted(self):self.assertFalse(evaluate_realbook_sceneir(self.f(),self.d()).accepted)
