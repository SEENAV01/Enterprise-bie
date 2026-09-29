from media_helpers import *
class VisualTests(Base):
 def test_overlap_fixed(self):
  c=self.context();b,w=c.preview();r=read_request(c.task,b);res=eval_visual(r,c.root,c.dp.qa,as_of=NOW,**vh.options(r,c.dp.qa));self.assertEqual(res.layout.status,'CHECKS_PASSED');self.assertTrue(w['changes'])
 def test_text_font_and_clip_preserved(self):
  c=self.context();r=read_request(c.task,c.preview()[0]);a=c.bad.states[0].measurements[1];b=r.states[0].measurements[1]
  self.assertEqual((a.text,a.font_mpx,a.clip,a.foreground,a.background),(b.text,b.font_mpx,b.clip,b.foreground,b.background))
 def test_uneditable_objects_preserved(self):
  c=self.context();r=read_request(c.task,c.preview()[0]);self.assertEqual(r.states[0].measurements[0],c.bad.states[0].measurements[0]);self.assertEqual(r.states[0].measurements[2],c.bad.states[0].measurements[2])
 def test_source_relations_and_times_preserved(self):
  c=self.context();r=read_request(c.task,c.preview()[0]);self.assertEqual(r.source,c.bad.source);self.assertEqual(r.relations,c.bad.relations);self.assertEqual(r.states[0].end_ms,c.bad.states[0].end_ms)
 def test_glyph_boxes_translated(self):
  c=self.context();r=read_request(c.task,c.preview()[0]);a=c.bad.states[0].measurements[1];b=r.states[0].measurements[1]
  self.assertEqual(b.line_boxes[0].y-a.line_boxes[0].y,b.box.y-a.box.y);self.assertEqual(a.line_boxes[0].width,b.line_boxes[0].width)
 def test_immutable_captured_observations(self):
  c=self.context();r,_=vh.fake_capture(c.root,c.bad,c.dp.qa);self.assertError('MEDIA_REPAIR_OBSERVATIONS_IMMUTABLE',c.preview,r)
 def test_sampled_geometry_not_relabelled(self):
  c=self.context();r=replace(c.bad,states=(replace(c.bad.states[0],geometry_mode='sampled'),));self.assertError('MEDIA_REPAIR_OBSERVATIONS_IMMUTABLE',c.preview,r)
 def test_shift_budget(self):
  c=self.context();p=replace(c.dp,permissions=(replace(c.dp.permissions[0],max_shift_mpx=0),));self.assertError('MEDIA_REPAIR_LAYOUT_UNSAT_OR_UNSUPPORTED',c.preview,p=p)
 def test_tiny_region_escalates(self):
  c=self.context();p=replace(c.dp,permissions=(replace(c.dp.permissions[0],region=Rect(0,0,1000,1000)),));self.assertError('MEDIA_REPAIR_LAYOUT_UNSAT_OR_UNSUPPORTED',c.preview,p=p)
 def test_hidden_content_not_unhidden_as_evidence(self):
  c=self.context();s=c.bad.states[0];r=replace(c.bad,states=(replace(s,measurements=(replace(s.measurements[0],displayed=False),)+s.measurements[1:]),));self.assertError('MEDIA_REPAIR_VIS_UNSUPPORTED',c.preview,r)
 def test_unsupported_style_requires_redesign(self):
  c=self.context();s=c.bad.states[0];r=replace(c.bad,states=(replace(s,measurements=(replace(s.measurements[0],unsupported=('rotation',)),)+s.measurements[1:]),));self.assertError('MEDIA_REPAIR_VIS_UNSUPPORTED',c.preview,r)
 def test_missing_state(self):
  c=self.context();s=replace(c.bad.states[0],state_id='different');r=replace(c.bad,states=(s,));self.assertError('MEDIA_REPAIR_VIS_STATE_SCOPE',c.preview,r)
 def test_time_window_cannot_change(self):
  c=self.context();r=replace(c.bad,states=(replace(c.bad.states[0],end_ms=30000),));self.assertError('MEDIA_REPAIR_VIS_STATE_CONTEXT',c.preview,r)
 def test_element_inventory_cannot_change(self):
  c=self.context();r=replace(c.bad,elements=(replace(c.bad.elements[0],semantic_id='changed'),)+c.bad.elements[1:]);self.assertError('MEDIA_REPAIR_SEMANTIC_INVENTORY',c.preview,r)
 def test_missing_object_escalates(self):
  c=self.context();r=replace(c.bad,states=(replace(c.bad.states[0],measurements=c.bad.states[0].measurements[:2]),));self.assertError('MEDIA_REPAIR_VIS_OBJECT_SCOPE',c.preview,r)
 def test_font_floor_not_weakened(self):
  c=self.context();s=c.bad.states[0];r=replace(c.bad,states=(replace(s,measurements=(replace(s.measurements[0],font_mpx=1000),)+s.measurements[1:]),));self.assertError('MEDIA_REPAIR_VIS_POSTCHECK_BLOCKED',c.preview,r)
 def test_cannot_delete_content_to_reduce_clutter(self):
  c=self.context();p=replace(c.dp,qa=replace(c.dp.qa,limits=replace(c.dp.qa.limits,max_text_codepoints=1)));self.assertError('MEDIA_REPAIR_VIS_POSTCHECK_BLOCKED',c.preview,p=p)
 def test_output_bound(self):
  c=self.context();self.assertError('MEDIA_REPAIR_OUTPUT_LIMIT',c.preview,limits=Limits(max_generated_bytes=1))
 def test_deterministic(self):
  c=self.context();self.assertEqual(c.preview(),c.preview())
 def test_render_required_remains_false(self):
  c=self.context();w=c.preview()[1];self.assertFalse(w['actual_render_verified']);self.assertFalse(w['observations_rewritten'])
 def test_unsigned_reviews_remain_open(self):
  c=self.context();self.assertEqual(c.preview()[1]['unsigned_postcheck']['status'],'REVIEW_REQUIRED')

 def test_total_search_budget_counts_failed_positions(self):
  c=self.context();self.assertError('MEDIA_REPAIR_LAYOUT_BUDGET',c.preview,limits=Limits(max_layout_visits=1))
 def test_local_search_frontier_budget(self):
  c=self.context();self.assertError('MEDIA_REPAIR_LAYOUT_BUDGET',c.preview,limits=Limits(max_positions_per_object=1))
