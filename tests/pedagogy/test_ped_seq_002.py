import unittest
from bie.pedagogy.concept_clustering import cluster_concepts
class T(unittest.TestCase):
 def test_cluster(self): self.assertEqual(cluster_concepts({"b":["x"],"a":["x"]}),(("x",("a","b")),))
