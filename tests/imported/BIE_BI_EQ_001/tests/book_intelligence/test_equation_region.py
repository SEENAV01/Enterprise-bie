import unittest
from bie.document_intelligence.equation_region import *
class T(unittest.TestCase):
    def test_ok(self): self.assertTrue(validate(EquationRegion("e",1,(0,0,1,1),.9)))
    def test_page(self):
        with self.assertRaises(EquationRegionError): validate(EquationRegion("e",0,(0,0,1,1),1))
    def test_box(self):
        with self.assertRaises(EquationRegionError): validate(EquationRegion("e",1,(1,0,0,1),1))
    def test_conf(self):
        with self.assertRaises(EquationRegionError): validate(EquationRegion("e",1,(0,0,1,1),2))
if __name__=="__main__": unittest.main()
