import unittest
from bie.visual_intelligence.representation_core import *
from bie.visual_intelligence.rep001_candidates import *
def I(**kw):
 d=dict(intent_id='i',domain='physics',concept_ids=('c',),evidence_refs=('e',),reasoning_refs=('r',),semantic_tags=('structure',));d.update(kw);return SemanticIntent(**d)
class T(unittest.TestCase):
 def test_default(self):self.assertIn('diagram',[x.representation for x in generate(I())])
 def test_map(self):self.assertEqual(generate(I(spatial=True,semantic_tags=('geographic',)))[0].representation,'map')
 def test_timeline(self):self.assertEqual(generate(I(temporal=True,semantic_tags=('chronology',)))[0].representation,'timeline')
 def test_graph(self):self.assertEqual(generate(I(quantitative=True,semantic_tags=('data',)))[0].representation,'graph')
 def test_equation(self):self.assertIn('equation',[x.representation for x in generate(I(equation_present=True,semantic_tags=('equation',)))])
 def test_sim(self):self.assertIn('simulation',[x.representation for x in generate(I(dynamic=True,semantic_tags=('process',)))])
 def test_grounding(self):self.assertEqual(generate(I())[0].evidence_refs,('e',))
 def test_unique(self):
  x=generate(I(dynamic=True,quantitative=True,equation_present=True));self.assertEqual(len(x),len(set(a.representation for a in x)))
 def test_cap(self):self.assertLessEqual(len(generate(I(),2)),2)
 def test_badcap(self):
  with self.assertRaises(RepresentationError):generate(I(),0)
def add(n,domain,tags,exp):
 def t(self):
  x=I(domain=domain,semantic_tags=tags,spatial='geographic' in tags,temporal='chronology' in tags,quantitative='data' in tags,equation_present='equation' in tags);self.assertIn(exp,[a.representation for a in generate(x)])
 setattr(T,f'test_case_{n}',t)
for i,c in enumerate([('physics',('structure',),'diagram'),('mathematics',('data',),'graph'),('geography',('geographic',),'map'),('history',('chronology',),'timeline'),('chemistry',('equation',),'equation'),('biology',('process',),'diagram'),('economics',('data',),'graph'),('physics',('equation',),'equation'),('geography',('route','geographic'),'map'),('history',('event','chronology'),'timeline')]):add(i,*c)
