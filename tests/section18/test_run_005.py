import tempfile,unittest
from bie.infrastructure.persistence import PersistedEvent
from tests.section18.helpers import CONFIG,service
class Run005(unittest.TestCase):
 def test_timeline_uses_canonical_transition_events(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];s.persistence.append_event(rid,PersistedEvent(0,"PDF_INSPECTION","PENDING","READY",1,"2026-09-30T00:00:00+00:00","ready",[]));self.assertEqual(s.timeline(rid)["transition_events"][0]["to_state"],"READY")
 def test_timeline_keeps_control_events_separate(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];s.persistence.set_run_state(rid,"ACTIVE");s.request_control(rid,"PAUSE","operator pause");self.assertEqual(s.timeline(rid)["control_events"][0]["action"],"PAUSE")
 def test_empty_timeline_is_valid(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertEqual(s.timeline(rid)["transition_events"],[])
 def test_timeline_not_acceptance(self):
  with tempfile.TemporaryDirectory() as t:
   s=service(t);rid=s.create_run(CONFIG)["run_id"];self.assertFalse(s.timeline(rid)["product_accepted"])
