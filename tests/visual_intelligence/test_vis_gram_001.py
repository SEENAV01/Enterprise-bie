import sys, unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'app'))

from bie.visual_intelligence.grammar_contracts import VisualGrammar, make_plan, GrammarElementError, GrammarRelationError, GrammarValidationError
from bie.visual_intelligence.grammar_registry import VisualGrammarRegistry, GrammarRegistryError, GrammarNotFoundError, GrammarAmbiguityError


def grammar(gid='g.one', domain='physics', rep='vector', aliases=()):
    return VisualGrammar(gid, '1.0.0', (domain,), (rep,), ('point','arrow'), ('node',), aliases=aliases)

class T(unittest.TestCase):
    def test_register_get(self):
        r=VisualGrammarRegistry(); g=grammar(); r.register(g); self.assertEqual(r.get('g.one'), g)
    def test_alias(self):
        r=VisualGrammarRegistry(); g=grammar(aliases=('one',)); r.register(g); self.assertEqual(r.get('one').grammar_id,'g.one')
    def test_duplicate_id(self):
        r=VisualGrammarRegistry(); r.register(grammar());
        with self.assertRaises(GrammarRegistryError): r.register(grammar())
    def test_duplicate_alias(self):
        r=VisualGrammarRegistry(); r.register(grammar('g.one', aliases=('same',)))
        with self.assertRaises(GrammarRegistryError): r.register(grammar('g.two', aliases=('same',)))
    def test_unknown(self):
        with self.assertRaises(GrammarNotFoundError): VisualGrammarRegistry().get('missing')
    def test_resolve_exact(self):
        r=VisualGrammarRegistry(); r.register(grammar()); self.assertEqual(r.resolve(domain='physics',representation='vector').grammar.grammar_id,'g.one')
    def test_resolve_not_found(self):
        r=VisualGrammarRegistry(); r.register(grammar());
        with self.assertRaises(GrammarNotFoundError): r.resolve(domain='history',representation='timeline')
    def test_resolve_ambiguity(self):
        r=VisualGrammarRegistry(); r.register(grammar('g.one')); r.register(grammar('g.two'))
        with self.assertRaises(GrammarAmbiguityError): r.resolve(domain='physics',representation='vector')
    def test_snapshot_deterministic(self):
        r=VisualGrammarRegistry(); r.register(grammar('g.b')); r.register(grammar('g.a'))
        self.assertEqual(r.snapshot(), r.snapshot())
        self.assertEqual([g['grammar_id'] for g in r.snapshot()['grammars']], ['g.a','g.b'])
    def test_plan_grounded(self):
        g=grammar(); p=make_plan(g,evidence_refs=['src1'],reasoning_refs=['r1'],elements=[{'id':'n','role':'node','primitive':'point','source_ids':['src1'],'payload':{}}])
        self.assertTrue(p.review_required); self.assertFalse(p.accepted)
    def test_plan_fingerprint_deterministic(self):
        g=grammar(); kw=dict(evidence_refs=['src1'],reasoning_refs=['r1'],elements=[{'id':'n','role':'node','primitive':'point','source_ids':['src1'],'payload':{'b':2,'a':1}}])
        self.assertEqual(make_plan(g,**kw).fingerprint, make_plan(g,**kw).fingerprint)
    def test_missing_role(self):
        g=grammar();
        with self.assertRaises(GrammarElementError): make_plan(g,evidence_refs=['s'],reasoning_refs=['r'],elements=[{'id':'x','role':'other','primitive':'point','source_ids':['s']}])
    def test_bad_primitive(self):
        g=grammar();
        with self.assertRaises(GrammarElementError): make_plan(g,evidence_refs=['s'],reasoning_refs=['r'],elements=[{'id':'x','role':'node','primitive':'circle','source_ids':['s']}])
    def test_unbound_element_source(self):
        g=grammar();
        with self.assertRaises(GrammarElementError): make_plan(g,evidence_refs=['s'],reasoning_refs=['r'],elements=[{'id':'x','role':'node','primitive':'point','source_ids':['other']}])
    def test_relation_unknown_target(self):
        g=grammar();
        with self.assertRaises(GrammarRelationError): make_plan(g,evidence_refs=['s'],reasoning_refs=['r'],elements=[{'id':'x','role':'node','primitive':'point','source_ids':['s']}],relations=[{'id':'e','source':'x','target':'y','kind':'link','source_ids':['s']}])
    def test_empty_evidence_rejected(self):
        g=grammar();
        with self.assertRaises(GrammarValidationError): make_plan(g,evidence_refs=[],reasoning_refs=['r'],elements=[{'id':'x','role':'node','primitive':'point','source_ids':['s']}])

if __name__=='__main__': unittest.main()
