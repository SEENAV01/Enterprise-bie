import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))
from bie.visual_intelligence.chemistry_molecular_grammar import plan_molecule, CHEMISTRY_MOLECULAR_GRAMMAR
from bie.visual_intelligence.grammar_contracts import GrammarValidationError
class T(unittest.TestCase):
    def atoms(self): return [{'id':'o','element':'O','source_ids':['s']},{'id':'h1','element':'H','source_ids':['s']},{'id':'h2','element':'H','source_ids':['s']}]
    def bonds(self): return [{'source':'o','target':'h1','order':1,'source_ids':['s']},{'source':'o','target':'h2','order':1,'source_ids':['s']}]
    def test_identity(self): self.assertEqual(CHEMISTRY_MOLECULAR_GRAMMAR.grammar_id,'bie.vis.grammar.chemistry_molecular')
    def test_plan(self): self.assertEqual(len(plan_molecule(self.atoms(),self.bonds(),evidence_refs=['s'],reasoning_refs=['r']).relations),2)
    def test_formal_charge(self):
        a=self.atoms(); a[0]['formal_charge']=-1; p=plan_molecule(a,self.bonds(),evidence_refs=['s'],reasoning_refs=['r']); self.assertEqual(p.elements[0]['payload']['formal_charge'],-1)
    def test_bad_symbol(self):
        with self.assertRaises(GrammarValidationError): plan_molecule([{'id':'x','element':'xx','source_ids':['s']}],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_charge(self):
        a=self.atoms(); a[0]['formal_charge']=0.5
        with self.assertRaises(GrammarValidationError): plan_molecule(a,self.bonds(),evidence_refs=['s'],reasoning_refs=['r'])
    def test_unknown_bond_atom(self):
        with self.assertRaises(GrammarValidationError): plan_molecule(self.atoms(),[{'source':'o','target':'z','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_bad_order(self):
        with self.assertRaises(GrammarValidationError): plan_molecule(self.atoms(),[{'source':'o','target':'h1','order':4,'source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_self_bond_rejected(self):
        with self.assertRaises(GrammarValidationError): plan_molecule(self.atoms(),[{'source':'o','target':'o','source_ids':['s']}],evidence_refs=['s'],reasoning_refs=['r'])
    def test_stereo_warning(self): self.assertTrue(plan_molecule(self.atoms(),self.bonds(),evidence_refs=['s'],reasoning_refs=['r']).warnings)
    def test_explicit_stereo_no_warning(self): self.assertFalse(plan_molecule(self.atoms(),self.bonds(),evidence_refs=['s'],reasoning_refs=['r'],stereochemistry_explicit=True).warnings)
    def test_empty(self):
        with self.assertRaises(GrammarValidationError): plan_molecule([],[],evidence_refs=['s'],reasoning_refs=['r'])
    def test_deterministic(self): self.assertEqual(plan_molecule(self.atoms(),self.bonds(),evidence_refs=['s'],reasoning_refs=['r']).fingerprint,plan_molecule(self.atoms(),self.bonds(),evidence_refs=['s'],reasoning_refs=['r']).fingerprint)
if __name__=='__main__': unittest.main()
