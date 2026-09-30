from batch002_helpers import Batch002Base, attach_fixture_tests, q, date
from copy import deepcopy
from fractions import Fraction

@attach_fixture_tests
class HIST003Tests(Batch002Base):
    task="BIE-EVAL-HIST-003"

    def test_day_numbers_match_python_calendar_sample(self):
        from datetime import date as civil
        from bie.evaluation.benchmarks.domains.temporal import date_interval
        origin=date_interval(date(1,1,1))[0]
        for year in [1,4,100,400,1582,1600,1700,1900,2000,2024,2400,9999]:
            for month in range(1,13):
                self.assertEqual(civil(year,month,1).toordinal()-1,date_interval(date(year,month,1))[0]-origin)
    def test_one_bce_to_one_ce_consecutive_days(self):
        v=self.values({'op':'compare_dates','a':date(1,12,31,'BCE'),'b':date(1,1,1)});self.assertEqual(1,v['b_minus_a_days_min'])
    def test_year_precision_not_point_date(self):
        v=self.values({'op':'compare_dates','a':date(2000),'b':date(2000,7,1)});self.assertEqual('OVERLAPPING_OR_UNCERTAIN',v['relation']);self.assertLess(v['b_minus_a_days_min'],0);self.assertGreater(v['b_minus_a_days_max'],0)
    def test_month_precision_bounds_account_for_leap_year(self):
        from bie.evaluation.benchmarks.domains.temporal import date_interval
        a,b=date_interval(date(2000,2));self.assertEqual(29,b-a+1);a,b=date_interval(date(1900,2));self.assertEqual(28,b-a+1)
    def test_same_day_ties_not_unique_order(self):
        v=self.values({'op':'partial_order','events':[{'id':'A','date':date(2000,1,1)},{'id':'B','date':date(2000,1,1)}]});self.assertFalse(v['unique_total_order']);self.assertEqual([['A','B']],v['same_day'])
    def test_partial_order_permutation_invariant(self):
        d=deepcopy(next(c.inputs for c in self.cases() if c.inputs['op']=='partial_order'));v=self.values(d);d['events'].reverse();self.assertEqual(v,self.values(d))
    def test_duplicate_event_id_refused(self):
        self.rejected({'op':'partial_order','events':[{'id':'A','date':date(2000)},{'id':'A','date':date(2001)}]},'DUPLICATE_EVENT')
    def test_irrelevant_day_with_year_precision_refused(self):
        d={'op':'compare_dates','a':date(2000),'b':date(2001)};d['a']['day']=1;self.rejected(d,'INVALID_FIELDS')
    def test_era_must_be_explicit(self):self.rejected({'op':'year_difference','a_year':1,'a_era':'AD?','b_year':1,'b_era':'CE'},'UNSUPPORTED_ENUM')
    def test_far_negative_astronomical_year_leap_spacing(self):
        from bie.evaluation.benchmarks.domains.temporal import date_interval
        for year in [1,2,400,4800,5000,9998]:
            a,b=date_interval(date(year,None,None,'BCE'));self.assertIn(b-a+1,[365,366])
