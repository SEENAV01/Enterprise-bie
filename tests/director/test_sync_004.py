import unittest
from dataclasses import replace
from bie.director.graph_narration_sync import *
from sync_fixtures import graph_case


class GraphSyncTests(unittest.TestCase):
    def test_axes_trace_and_point_keep_exact_source_data(self):
        c,v,g,rows=graph_case(); p=sync_graph_narration(c,v,[g],rows)
        self.assertFalse(p.issues)
        trace=next(x for x in p.cues if x.kind=='TRACE_SERIES')
        points=dict(trace.parameters)['waypoints']
        self.assertEqual([x[0] for x in points],['p0','p1','p2'])
        self.assertEqual([(x[2],x[3]) for x in points],[(0,0),(1,2),(2,4)])
        self.assertEqual([(x[4],x[5]) for x in points],[(0,0),(.5,.5),(1,1)])
        self.assertEqual(points[0][1],trace.window.start_ms)
        self.assertEqual(points[-1][1],trace.window.end_ms)

    def test_units_or_values_revision_invalidates_intent(self):
        c,v,g,rows=graph_case()
        for changed in (replace(g,x_axis=replace(g.x_axis,unit='ms')),replace(g,revision='new')):
            with self.assertRaises(ValueError): sync_graph_narration(c,v,[changed],rows)

    def test_axes_must_precede_trace(self):
        c,v,g,rows=graph_case(); p=sync_graph_narration(c,v,[g],rows[1:])
        self.assertIn('GRAPH_AXES_NOT_INTRODUCED',{i.code for i in p.issues})

    def test_unknown_points_series_and_reverse_trace_rejected(self):
        c,v,g,rows=graph_case()
        for r in (replace(rows[1],series_id='missing'),replace(rows[1],point_ids=('p0','missing')),
                  replace(rows[1],point_ids=('p2','p0'))):
            with self.assertRaises(ValueError): sync_graph_narration(c,v,[g],(rows[0],r))

    def test_range_uses_ordered_source_endpoints(self):
        c,v,g,rows=graph_case()
        r=replace(rows[2],action='HIGHLIGHT_RANGE',point_ids=('p0','p2'))
        p=sync_graph_narration(c,v,[g],rows[:2]+(r,))
        self.assertEqual(len(dict(next(x for x in p.cues if x.kind=='HIGHLIGHT_RANGE').parameters)['waypoints']),3)
        with self.assertRaises(ValueError): sync_graph_narration(c,v,[g],rows[:2]+(replace(r,point_ids=('p2','p0')),))

    def test_invalid_axis_and_nonfinite_points_rejected(self):
        c,v,g,rows=graph_case()
        invalid=(replace(g,x_axis=replace(g.x_axis,maximum=0)),replace(g,x_axis=replace(g.x_axis,scale='LOG')),
                 replace(g,y_axis=replace(g.y_axis,maximum=float('inf'))),
                 replace(g,series=(replace(g.series[0],points=(replace(g.series[0].points[0],x=True),)),)))
        for bad in invalid:
            with self.subTest(bad=bad),self.assertRaises(ValueError): sync_graph_narration(c,v,[bad],rows)

    def test_log_axis_normalization_and_unit_retention(self):
        c,v,g,rows=graph_case()
        points=tuple(replace(p,x=x) for p,x in zip(g.series[0].points,(1,10,100)))
        g=replace(g,x_axis=replace(g.x_axis,minimum=1,maximum=100,scale='LOG'),series=(replace(g.series[0],points=points),))
        rows=tuple(replace(r,graph_fingerprint=g.fingerprint()) for r in rows)
        p=sync_graph_narration(c,v,[g],rows)
        middle=dict(next(x for x in p.cues if x.kind=='TRACE_SERIES').parameters)['waypoints'][1]
        self.assertAlmostEqual(middle[4],.5)

    def test_ungrounded_series_point_rejected(self):
        c,v,g,rows=graph_case()
        bad=replace(g,series=(replace(g.series[0],points=(replace(g.series[0].points[0],evidence_ids=('outside',)),)),))
        with self.assertRaises(ValueError): sync_graph_narration(c,v,[bad],rows)

    def test_generators_and_semantic_acceptance_boundary(self):
        c,v,g,rows=graph_case()
        a=sync_graph_narration(c,v,[g],rows); b=sync_graph_narration(c,v,(x for x in [g]),reversed(rows))
        self.assertEqual(a.fingerprint(),b.fingerprint())
        self.assertFalse(a.accepted)
        self.assertIn('GRAPH_DATA_MEANING_AND_RENDER_REQUIRE_QA',a.review_reasons)
