import math,unittest
from bie.compiler.chart_geometry import chart_geometry,TOP,BOTTOM
from bie.compiler.chart_compiler import compile_chart_element
from tests.compiler.h1_test_support import element,runtime_tree,nodes

class ChartGeometryTests(unittest.TestCase):
    def props(self,kind='bar',values=None):
        values=[-2,0,3] if values is None else values
        return {'chart_kind':kind,'categories':[str(i) for i in range(len(values))],'values':values}
    def test_mixed_domain_preserves_sign(self):self.assertEqual(chart_geometry(self.props())['domain'],[-2,3])
    def test_negative_below_baseline(self):
        g=chart_geometry(self.props());b=g['bars'][0];self.assertEqual(b['y'],g['baseline']);self.assertGreater(b['height'],0)
    def test_positive_above_baseline(self):
        g=chart_geometry(self.props());b=g['bars'][2];self.assertLess(b['y'],g['baseline']);self.assertAlmostEqual(b['y']+b['height'],g['baseline'])
    def test_zero_has_zero_height(self):self.assertEqual(chart_geometry(self.props())['bars'][1]['height'],0)
    def test_all_positive_zero_baseline_bottom(self):self.assertEqual(chart_geometry(self.props(values=[1,2]))['baseline'],BOTTOM)
    def test_all_negative_zero_baseline_top(self):self.assertEqual(chart_geometry(self.props(values=[-1,-2]))['baseline'],TOP)
    def test_all_zero_finite_domain(self):self.assertEqual(chart_geometry(self.props(values=[0,0]))['domain'],[-1,1])
    def test_line_no_bar_geometry(self):
        g=chart_geometry(self.props('line'));self.assertFalse(g['bars']);self.assertTrue(g['line_points']);self.assertGreater(g['points'][0]['y'],g['baseline'])
    def test_area_closes_to_signed_baseline(self):
        g=chart_geometry(self.props('area'));self.assertTrue(g['area_points']);self.assertIn(f",{g['baseline']:.12g}",g['area_points'])
    def test_scatter_uses_numeric_spacing(self):
        p=self.props('scatter',[1,1,1]);p['x_values']=[0,1,10];g=chart_geometry(p);x=[v['x'] for v in g['points']];self.assertAlmostEqual((x[2]-x[1])/(x[1]-x[0]),9)
    def test_scatter_x_values_required(self):
        with self.assertRaises(ValueError):chart_geometry(self.props('scatter'))
    def test_scatter_length_mismatch(self):
        p=self.props('scatter');p['x_values']=[1]
        with self.assertRaises(ValueError):chart_geometry(p)
    def test_pie_fractions_sum_to_one(self):self.assertAlmostEqual(sum(x['fraction'] for x in chart_geometry(self.props('pie',[1,2,3]))['slices']),1)
    def test_pie_zero_slice_preserves_source_legend(self):
        g=chart_geometry(self.props('pie',[0,1]));self.assertEqual(g['values'],[0,1]);self.assertEqual(len(g['slices']),1)
    def test_pie_single_positive_is_full_circle(self):self.assertEqual(chart_geometry(self.props('pie',[4]))['slices'][0]['path'].count(' A '),2)
    def test_pie_signed_data_rejected(self):
        with self.assertRaisesRegex(ValueError,'PIE_NEGATIVE'):chart_geometry(self.props('pie',[-1,2]))
    def test_pie_zero_total_rejected(self):
        with self.assertRaisesRegex(ValueError,'PIE_ZERO'):chart_geometry(self.props('pie',[0,0]))
    def test_numeric_strings_rejected(self):
        with self.assertRaises(ValueError):chart_geometry(self.props(values=['3']))
    def test_bool_rejected(self):
        with self.assertRaises(ValueError):chart_geometry(self.props(values=[True]))
    def test_nonfinite_rejected(self):
        for v in [math.inf,-math.inf,math.nan]:
            with self.subTest(v=v),self.assertRaises(ValueError):chart_geometry(self.props(values=[v]))
    def test_input_budget_rejected(self):
        with self.assertRaises(ValueError):chart_geometry(self.props(values=[1]*2001))
    def test_unknown_kind_rejected(self):
        with self.assertRaises(ValueError):chart_geometry(self.props('radar'))
    def test_empty_rejected(self):
        with self.assertRaises(ValueError):chart_geometry(self.props(values=[]))
    def test_length_mismatch_rejected(self):
        p=self.props();p['categories'].pop()
        with self.assertRaises(ValueError):chart_geometry(p)
    def test_unused_numeric_x_not_ignored(self):
        p=self.props();p['x_values']=[1,2,3]
        with self.assertRaises(ValueError):chart_geometry(p)
    def test_actual_tsx_bar_rectangles_have_signed_coordinates(self):
        g=chart_geometry(self.props());tree=runtime_tree(compile_chart_element(element('chart',self.props())));bars=nodes(tree,'rect');self.assertEqual(len(bars),3);self.assertEqual(bars[0]['props']['y'],g['baseline'])
    def test_actual_tsx_line_is_not_bars(self):
        tree=runtime_tree(compile_chart_element(element('chart',self.props('line'))));self.assertFalse(nodes(tree,'rect'));self.assertEqual(len(nodes(tree,'polyline')),1)
    def test_actual_tsx_area_has_polygon(self):self.assertEqual(len(nodes(runtime_tree(compile_chart_element(element('chart',self.props('area')))),'polygon')),1)
    def test_actual_tsx_pie_has_native_slices(self):self.assertEqual(len(nodes(runtime_tree(compile_chart_element(element('chart',self.props('pie',[1,2])))),'path')),2)
    def test_equal_values_single_point_geometry_finite(self):
        for kind in ['bar','line','area']:
            g=chart_geometry(self.props(kind,[2]));self.assertTrue(all(math.isfinite(p['x']) and math.isfinite(p['y']) for p in g['points']))
    def test_large_finite_signed_data(self):
        g=chart_geometry(self.props(values=[-1e99,1e99]));self.assertTrue(all(math.isfinite(p['height']) for p in g['bars']))
    def test_dense_chart_is_review_blocked_not_silent(self):self.assertIn('CHART_DENSE_LABEL_LAYOUT_REQUIRES_REVIEW',compile_chart_element(element('chart',self.props(values=[1]*13))).warnings)
    def test_units_preserved(self):
        p=self.props();p['units']='₹ crore';self.assertEqual(chart_geometry(p)['units'],'₹ crore')
    def test_no_fallback_warning_or_acceptance(self):
        r=compile_chart_element(element('chart',self.props('line')));self.assertEqual(r.warnings,());self.assertFalse(r.accepted)

if __name__=='__main__':unittest.main()
