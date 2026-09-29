from h5_helpers import *
from bie.qa.media_runtime_v2.motion import *
class Motion(Case):
    def setup_trace(self,change=None,policy=None):
        p=policy or MotionPolicy(7,'6',(Track('mass','x',('0','1','2','3'),'0','3','10'),),('distance',))
        b=bind(p);rows=[dict(frame=i,timestamp=str(Fraction(i)/q(p.fps)),mode=p.mode,meaning_ids=list(p.required_meanings),values={'mass.x':str(bezier_value(p.tracks[0].controls,Fraction(i,p.frames-1)))},binding=asdict(b)) for i in range(p.frames)]
        if change:change(rows)
        r=ref(self.root,'trace.jsonl',b''.join(canonical_bytes(x)+b'\n' for x in rows),'trace',True)
        return p,b,r
    def check(self,change=None,p=None):
        p,b,r=self.setup_trace(change,p);return inspect_motion(self.root,r,b,p)
    def test_healthy_all_frames(self):
        r=self.check();self.assertTrue(r['technical_checks_clear']);self.assertEqual(r['report']['status'],'REVIEW_REQUIRED');self.unchanged(r)
    def test_cubic_nonendpoint_violation(self):self.assertEqual(enclose_cubic(('0','4','4','0'),'0','1'),'VIOLATION')
    def test_conservative_enclosure_abstains(self):self.assertEqual(enclose_cubic(('0','2','-2','0'),'-1','1',depth=0),'UNRESOLVED')
    def test_continuous_range_clear(self):self.assertEqual(enclose_cubic(('0','1','2','3'),'0','3'),'CLEAR')
    def test_intermediate_trace_defect(self):self.has(self.check(lambda r:r[3]['values'].update({'mass.x':'5'})),'H5_STATE_TRAJECTORY_MISMATCH')
    def test_meaning_loss_reduced_motion(self):self.has(self.check(lambda r:r[3].update(meaning_ids=['wrong'])),'H5_REDUCED_MEANING_LOSS')
    def test_missing_last_frame(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_MISSING_FRAME'):self.check(lambda r:r.pop())
    def test_missing_interior_frame(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_FRAME_COVERAGE'):self.check(lambda r:r.pop(2))
    def test_repeated_frame(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_FRAME_COVERAGE'):self.check(lambda r:r.insert(2,r[1]))
    def test_foreign_binding(self):
        with self.assertRaisesRegex(ContractError,'NATIVE_BINDING_MISMATCH'):self.check(lambda r:r[1]['binding'].update(run_id='foreign'))
    def test_clock_drift(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_CLOCK'):self.check(lambda r:r[1].update(timestamp='1/7'))
    def test_unknown_object(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_OBJECT_INVENTORY'):self.check(lambda r:r[1]['values'].update(extra='2'))
    def test_mode_mismatch(self):
        with self.assertRaisesRegex(ContractError,'H5_STATE_MODE'):self.check(lambda r:r[1].update(mode='reduced'))
    def test_reduced_speed_is_enforced(self):
        p=MotionPolicy(7,'6',(Track('mass','x',('0','1','2','3'),'0','3','4'),),('distance',),mode='reduced')
        self.has(self.check(p=p),'H5_STATE_SPEED')
    def test_native_event_contract_executed(self):
        e=Event('event','move',('mass',),0,1000,'explain',('source',),('reason',),1)
        r=native_event_check((e,));self.assertTrue(r.qa_id)
    def test_native_overlap_is_preserved(self):
        e=Event('event','move',('mass',),0,1000,'explain',('source',),('reason',),1)
        p,b,t=self.setup_trace();r=inspect_motion(self.root,t,b,p,native_events=(e,replace(e,event_id='second')))
        self.has(r,'H5_NATIVE_TEMPORAL_CONFLICT')
    def test_unsupported_spring_not_linearized(self):
        with self.assertRaises(ContractError):Track('a','spring',('0','1','2','3'),'0','3','10')
    def test_duplicate_tracks(self):
        t=Track('a','x',('0','1','2','3'),'0','3','10')
        with self.assertRaises(ContractError):MotionPolicy(2,'1',(t,t),('a',))
    def test_exact_fractional_clock(self):
        p=MotionPolicy(7,'30000/1001',(Track('mass','x',('0','1','2','3'),'0','3','100'),),('distance',));self.assertTrue(self.check(p=p)['technical_checks_clear'])
    def test_rational_types_no_bool_float(self):
        for v in (True,0.1,'NaN','1/0','2+2','1.2'):
            with self.subTest(value=v),self.assertRaises(ContractError):q(v)
