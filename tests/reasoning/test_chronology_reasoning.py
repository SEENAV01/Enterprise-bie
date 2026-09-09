import unittest
from bie.reasoning.decision_contracts import EvidenceRef
from bie.reasoning.chronology_reasoning import Event, TimeSpan, year, calendar_date, chronology, relation

class ChronologyTests(unittest.TestCase):
    def setUp(self):self.refs=(EvidenceRef("history:1","primary",.9),)
    def e(self,id,t):return Event(id,id,t,("history:1",))
    def test_bce_direction(self):self.assertEqual(relation(year("100 BCE"),year("44 BCE")),"before")
    def test_era_boundary(self):self.assertEqual(year("1 CE").earliest-year("1 BCE").earliest,1)
    def test_no_historical_zero(self):
        for value in ("0","0 BCE","-44","44 XYZ",True):
            with self.subTest(value=value),self.assertRaises(ValueError):year(value)
    def test_leap_day(self):self.assertEqual(calendar_date("2024-03-01").earliest-calendar_date("2024-02-28").earliest,2)
    def test_invalid_date(self):
        with self.assertRaises(ValueError):calendar_date("2023-02-29")
    def test_mixed_axes_refused(self):
        with self.assertRaises(ValueError):chronology([self.e("A",year("2000")),self.e("B",calendar_date("2000-01-01"))],self.refs)
    def test_definite_order(self):
        r=chronology([self.e("C",year("1 CE")),self.e("A",year("10 BCE")),self.e("B",year("1 BCE"))],self.refs)
        self.assertEqual(r.value["display_order"],["A","B","C"]);self.assertEqual(len(r.value["proven_before"]),3)
    def test_overlapping_uncertainty(self):
        r=chronology([self.e("A",TimeSpan(100,110)),self.e("B",TimeSpan(105,120))],self.refs)
        self.assertEqual(r.status,"AMBIGUOUS");self.assertEqual(r.value["proven_before"],[])
    def test_touching_uncertainty_is_not_simultaneous(self):self.assertEqual(relation(TimeSpan(1,2),TimeSpan(2,3)),"indeterminate")
    def test_exact_simultaneous(self):
        r=chronology([self.e("A",year("1200")),self.e("B",year("1200"))],self.refs)
        self.assertEqual(r.value["simultaneous"],[["A","B"]])
    def test_open_bounds(self):self.assertEqual(relation(TimeSpan(None,100),TimeSpan(101,None)),"before")
    def test_unknown_time(self):
        r=chronology([self.e("A",TimeSpan(None,None)),self.e("B",year("100"))],self.refs)
        self.assertEqual(r.status,"AMBIGUOUS")
    def test_reversed_and_boolean_bounds(self):
        for a,b in [(4,3),(True,3),(1.2,3)]:
            with self.subTest(a=a,b=b),self.assertRaises(ValueError):TimeSpan(a,b)
    def test_duplicate_event(self):
        with self.assertRaises(ValueError):chronology([self.e("A",year("1")),self.e("A",year("2"))],self.refs)
    def test_permutation_identity(self):
        events=[self.e("A",year("1")),self.e("B",year("2"))]
        self.assertEqual(chronology(events,self.refs).result_id,chronology(events[::-1],self.refs).result_id)
