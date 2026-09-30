from batch003_helpers import Batch002Base,attach_fixture_tests
from copy import deepcopy
@attach_fixture_tests
class DATA001Tests(Batch002Base):
    task='BIE-EVAL-DATA-001'
    def chart(self):return deepcopy(next(c.inputs for c in self.cases() if c.inputs.get('op')=='chart_fidelity'))
    def test_summary_negative_values_exact(self):
        v=self.values({'op':'summary','rows':[{'id':'a','value':-2},{'id':'b','value':1}],'missing_policy':'reject'});self.assertEqual('-1/2',v['mean']);self.assertEqual('-1/2',v['median'])
    def test_duplicate_row_ids_rejected(self):
        self.rejected({'op':'summary','rows':[{'id':'a','value':1},{'id':'a','value':2}],'missing_policy':'reject'},'DUPLICATE_ROW_ID')
    def test_zero_weight_row_not_influence_mean(self):
        v=self.values({'op':'weighted_mean','rows':[{'id':'a','value':999,'weight':0},{'id':'b','value':4,'weight':1}]});self.assertEqual('4',v['weighted_mean'])
    def test_unannounced_unit_conversion_fails(self):
        d=self.chart();d['chart_unit']='other';self.assertFalse(self.values(d)['data_faithful'])
    def test_missing_chart_point_detected(self):
        d=self.chart();d['chart_points'].pop();self.assertIn('MISSING_POINT',{x['reason'] for x in self.values(d)['defects']})
    def test_extra_chart_point_detected(self):
        d=self.chart();d['chart_points'].append({'id':'extra','value':1});self.assertIn('EXTRA_POINT',{x['reason'] for x in self.values(d)['defects']})
    def test_chart_wrong_value_detected(self):
        d=self.chart();d['chart_points'][0]['value']=999;self.assertIn('CELL_VALUE_MISMATCH',{x['reason'] for x in self.values(d)['defects']})
    def test_chart_axis_cannot_hide_source_value(self):
        d=self.chart();d['y_axis']['maximum']=1;self.assertFalse(self.values(d)['data_faithful'])
    def test_log_axis_nonpositive_rejected(self):
        d=self.chart();d['y_axis']={'minimum':0,'maximum':100,'scale':'log'};self.rejected(d,'INVALID_AXIS')
    def test_negative_percentage_base_not_silently_used(self):
        self.rejected({'op':'percent_change','before':-2,'after':3},'QUANTITY_OUT_OF_PROFILE')
