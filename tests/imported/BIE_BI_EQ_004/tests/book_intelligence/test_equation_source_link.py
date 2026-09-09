import unittest
from bie.document_intelligence.equation_source_link import *
class T(unittest.TestCase):
    def x(self): return EquationSourceLink("e","a"*64,1,"r","x=1",.9)
    def test_ok(self): self.assertTrue(validate(self.x()))
    def test_hash(self):
        with self.assertRaises(EquationLinkError): validate(EquationSourceLink("e","x",1,"r","x",1))
    def test_region(self):
        with self.assertRaises(EquationLinkError): validate(EquationSourceLink("e","a"*64,1,"","x",1))
    def test_latex(self):
        with self.assertRaises(EquationLinkError): validate(EquationSourceLink("e","a"*64,1,"r","",1))
    def test_conf(self):
        with self.assertRaises(EquationLinkError): validate(EquationSourceLink("e","a"*64,1,"r","x",2))
if __name__=="__main__": unittest.main()
