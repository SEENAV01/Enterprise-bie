import tempfile,unittest,json
from bie.infrastructure.persistence import PersistedArtifactRecord
from bie.product_app.graph_views import GraphArtifactError,GraphArtifactViewer
from tests.section18.helpers import CONFIG,graph_artifact,service
class Graph002(unittest.TestCase):
 def test_prerequisite_graph_reads_evidence_edges(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];aid=graph_artifact(s,rid,"prerequisite");v=GraphArtifactViewer(s.persistence,s.cas).load(rid,aid,"prerequisite");self.assertEqual(v["edges"][0]["evidence_refs"],["ev:1"])
 def test_missing_node_edge_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];body={"schema_version":"bie.graph.v1","nodes":[{"id":"a","label":"A","source_refs":["src"]}],"edges":[{"source":"a","target":"missing","relation":"requires","evidence_refs":["ev"]}]};raw=json.dumps(body).encode();blob=s.cas.put_bytes(raw);s.persistence.register_artifact(PersistedArtifactRecord("bad","knowledge.prerequisite_graph",blob.algorithm,blob.digest,blob.size,rid,"PDF_INSPECTION",False,{},[]))
   with self.assertRaises(GraphArtifactError):GraphArtifactViewer(s.persistence,s.cas).load(rid,"bad","prerequisite")
 def test_duplicate_node_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];body={"schema_version":"bie.graph.v1","nodes":[{"id":"a","label":"A","source_refs":["x"]},{"id":"a","label":"B","source_refs":["y"]}],"edges":[]};raw=json.dumps(body).encode();blob=s.cas.put_bytes(raw);s.persistence.register_artifact(PersistedArtifactRecord("dup","knowledge.prerequisite_graph",blob.algorithm,blob.digest,blob.size,rid,"PDF_INSPECTION",False,{},[]))
   with self.assertRaises(GraphArtifactError):GraphArtifactViewer(s.persistence,s.cas).load(rid,"dup","prerequisite")
 def test_view_never_claims_acceptance(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];aid=graph_artifact(s,rid,"prerequisite");self.assertFalse(GraphArtifactViewer(s.persistence,s.cas).load(rid,aid,"prerequisite")["product_accepted"])
