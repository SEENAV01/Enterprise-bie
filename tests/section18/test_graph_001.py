import tempfile,unittest
from bie.product_app.graph_views import GraphArtifactError,GraphArtifactViewer
from bie.product_app.html_views import graph_html
from tests.section18.helpers import CONFIG,graph_artifact,service
class Graph001(unittest.TestCase):
 def test_concept_graph_reads_bound_artifact(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];aid=graph_artifact(s,rid,"concept");v=GraphArtifactViewer(s.persistence,s.cas).load(rid,aid,"concept");self.assertEqual(len(v["nodes"]),2);self.assertTrue(v["source_bound"])
 def test_concept_wrong_kind_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];aid=graph_artifact(s,rid,"prerequisite")
   with self.assertRaises(GraphArtifactError):GraphArtifactViewer(s.persistence,s.cas).load(rid,aid,"concept")
 def test_cross_run_artifact_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);r1=s.create_run(CONFIG)["run_id"];aid=graph_artifact(s,r1,"concept");s.id_factory=lambda:"fedcba9876543210";r2=s.create_run(CONFIG)["run_id"]
   with self.assertRaises(GraphArtifactError):GraphArtifactViewer(s.persistence,s.cas).load(r2,aid,"concept")
 def test_html_is_accessible_and_escaped(self):
  h=graph_html("Concept graph",{"nodes":[{"id":"a","label":"<A>","source_refs":["src"]}],"edges":[]});self.assertIn('aria-labelledby="graph-heading"',h);self.assertNotIn("<A>",h)
