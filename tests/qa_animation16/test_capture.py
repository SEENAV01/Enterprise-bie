"""Synthetic PNG/observation fixtures test validation; these are NOT browser runs."""
from ani_helpers import *
from fractions import Fraction
from io import BytesIO
import json,os
from PIL import Image
from bie.qa.animation_v2.metrics import frame_time_ms
from bie.qa.animation_v2.capture_evidence import expected_value,validate_png

def synthetic_capture(root,r,p,edit=None,*,format='PNG',dimensions=None):
    mode=p.modes[0];spec=p.captures[0]
    html=artifact(root,'capture/synthetic.html',b'<p>SYNTHETIC capture fixture, not a browser result.</p>','synthetic-html')
    shots=[];frames=[]
    for i in spec.frame_indices:
        buf=BytesIO();Image.new('RGB',dimensions or (mode.width_px,mode.height_px)).save(buf,format=format)
        shot=artifact(root,f'capture/frame-{i}.png',buf.getvalue(),f'synthetic-png-{i}');shots.append(shot)
        time=frame_time_ms(i,mode.fps)
        row=dict(frame_index=i,time_numerator=time.numerator,time_denominator=time.denominator,screenshot_sha256=shot.sha256,objects=[])
        for obj in p.objects:
            values={key:int(expected_value(r,mode.mode_id,obj.object_id,key,time) or 0) for key in ('x_mpx','y_mpx','opacity_ppm')}
            row['objects'].append(dict(object_id=obj.object_id,**values,width_mpx=40000,height_mpx=40000,displayed=True))
        frames.append(row)
    data=dict(schema_version='1.0.0',mode='paused-css-samples',plan_digest=r.plan_digest,policy_digest=p.content_digest,
        mode_id=mode.mode_id,html_sha256=html.sha256,renderer='SYNTHETIC - no browser',viewport=[mode.width_px,mode.height_px],frames=frames,unsupported=[])
    if edit:edit(data)
    obs=artifact(root,'capture/observations.json',canonical_bytes(data),'synthetic-observations')
    return CaptureRef('synthetic-capture',mode.mode_id,html,obs,tuple(shots))

class CaptureTests(FixtureCase):
    def captured(self,edit=None,**kw):
        c=synthetic_capture(self.root,self.r,self.p,edit,**kw);r=replace(self.r,captures=(c,));return r,c
    def changed(self,fn,code):
        r,_=self.captured(fn);self.assertCode(self.check(r),code)
    def test_sample_receipt_never_complete_media(self):
        r,_=self.captured();q=self.check(r);self.assertEqual(q.status,'REVIEW_REQUIRED');self.assertCode(q,'ANI_SAMPLED_MEDIA_ONLY');self.assertEqual(q.verified_capture_ids,('synthetic-capture',))
    def test_capture_ids_and_inspected_bytes(self):
        r,c=self.captured();q=self.check(r);self.assertTrue({x.artifact_id for x in (c.html,c.observations)+c.screenshots}<=set(q.temporal.inspected_artifact_ids))
    def test_wrong_plan(self):self.changed(lambda d:d.update(plan_digest='0'*64),'ANI_CAPTURE_CONTEXT')
    def test_wrong_policy(self):self.changed(lambda d:d.update(policy_digest='0'*64),'ANI_CAPTURE_CONTEXT')
    def test_wrong_html_binding(self):self.changed(lambda d:d.update(html_sha256='0'*64),'ANI_CAPTURE_HTML_BINDING')
    def test_wrong_viewport(self):self.changed(lambda d:d.update(viewport=[320,240]),'ANI_CAPTURE_VIEW')
    def test_wrong_mode(self):self.changed(lambda d:d.update(mode_id='other'),'ANI_CAPTURE_VIEW')
    def test_wrong_capture_kind(self):self.changed(lambda d:d.update(mode='simulated-runtime'),'ANI_CAPTURE_KIND')
    def test_extra_root_field(self):self.changed(lambda d:d.update(accepted=True),'ANI_CAPTURE_FIELDS')
    def test_invalid_renderer(self):self.changed(lambda d:d.update(renderer=''),'ANI_CAPTURE_RENDERER')
    def test_wrong_clock(self):self.changed(lambda d:d['frames'][1].update(time_numerator=501),'ANI_CAPTURE_CLOCK_OR_ORDER')
    def test_noncanonical_rational_time(self):
        def edit(d):d['frames'][1].update(time_numerator=1000,time_denominator=2)
        self.changed(edit,'ANI_CAPTURE_CLOCK_OR_ORDER')
    def test_swapped_frames(self):self.changed(lambda d:d['frames'].reverse(),'ANI_CAPTURE_CLOCK_OR_ORDER')
    def test_missing_frame(self):self.changed(lambda d:d['frames'].pop(),'ANI_CAPTURE_SAMPLE_COUNT')
    def test_shot_hash_mismatch(self):self.changed(lambda d:d['frames'][2].update(screenshot_sha256='0'*64),'ANI_CAPTURE_SCREENSHOT_BINDING')
    def test_missing_object(self):self.changed(lambda d:d['frames'][1].update(objects=[]),'ANI_CAPTURE_OBJECT_INVENTORY')
    def test_duplicate_object(self):self.changed(lambda d:d['frames'][0]['objects'].append(dict(d['frames'][0]['objects'][0])),'ANI_CAPTURE_DUPLICATE_OBJECT')
    def test_extra_object(self):
        def edit(d):q=dict(d['frames'][0]['objects'][0]);q['object_id']='unapproved';d['frames'][0]['objects'].append(q)
        self.changed(edit,'ANI_CAPTURE_OBJECT_INVENTORY')
    def test_hidden_object(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(displayed=False),'ANI_CAPTURE_HIDDEN_OBJECT')
    def test_trajectory_mismatch(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(x_mpx=220000),'ANI_CAPTURE_TRAJECTORY_MISMATCH')
    def test_opacity_mismatch(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(opacity_ppm=0),'ANI_CAPTURE_TRAJECTORY_MISMATCH')
    def test_exact_tolerance_boundary(self):
        r,_=self.captured(lambda d:d['frames'][1]['objects'][0].update(x_mpx=81500));self.assertNotIn('ANI_CAPTURE_TRAJECTORY_MISMATCH',codes(self.check(r)))
    def test_one_millipixel_over_tolerance(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(x_mpx=81501),'ANI_CAPTURE_TRAJECTORY_MISMATCH')
    def test_bool_not_coordinate(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(x_mpx=True),'INVALID_INTEGER')
    def test_display_not_integer(self):self.changed(lambda d:d['frames'][1]['objects'][0].update(displayed=1),'ANI_CAPTURE_OBJECT_TYPE')
    def test_unknown_paint_requires_review(self):
        r,_=self.captured(lambda d:d.update(unsupported=['unmeasured-complex-paint']));self.assertCode(self.check(r),'ANI_CAPTURE_UNSUPPORTED')
    def test_unsupported_fields_invalid(self):self.changed(lambda d:d.update(unsupported=[123]),'ANI_CAPTURE_UNSUPPORTED_FIELDS')
    def test_png_dimensions(self):
        r,_=self.captured(dimensions=(64,64));self.assertCode(self.check(r),'ANI_CAPTURE_IMAGE_DIMENSIONS')
    def test_not_png(self):
        r,_=self.captured(format='JPEG');self.assertCode(self.check(r),'ANI_CAPTURE_IMAGE_DIMENSIONS')
    def test_invalid_png_bytes(self):
        with self.assertRaises(ContractError):validate_png(b'not a png',640,360)
    def test_modified_measurement_bytes(self):
        r,c=self.captured();(self.root/c.observations.path).write_bytes(b'{}');self.assertEqual(self.check(r).status,'BLOCKED')
    def test_modified_screenshot_bytes(self):
        r,c=self.captured();(self.root/c.screenshots[0].path).write_bytes(b'bad');self.assertEqual(self.check(r).status,'BLOCKED')
    def test_modified_html_bytes(self):
        r,c=self.captured();(self.root/c.html.path).write_bytes(b'<p>changed</p>');self.assertEqual(self.check(r).status,'BLOCKED')
    def test_missing_screenshot(self):
        r,c=self.captured();(self.root/c.screenshots[0].path).unlink();self.assertEqual(self.check(r).status,'BLOCKED')
    def test_symlink_screenshot(self):
        r,c=self.captured();f=self.root/c.screenshots[0].path;data=f.read_bytes();f.unlink();out=self.root/'external';out.write_bytes(data);f.symlink_to(out);self.assertEqual(self.check(r).status,'BLOCKED')
    def test_hardlink_screenshot(self):
        r,c=self.captured();f=self.root/c.screenshots[0].path;os.link(f,self.root/'another-link');self.assertEqual(self.check(r).status,'BLOCKED')
    def test_sample_cannot_be_reused_for_changed_plan(self):
        r,_=self.captured();r=change_track(r,keyframes=(Keyframe(0,40000),Keyframe(2000,190000)));self.assertCode(self.check(r),'ANI_CAPTURE_CONTEXT')
    def test_sample_cannot_be_reused_for_changed_policy(self):
        r,_=self.captured();p=replace(self.p,policy_id='changed');self.assertCode(self.check(r,p),'ANI_CAPTURE_CONTEXT')
    def test_expected_value_after_endpoint(self):self.assertEqual(expected_value(self.r,'standard','marker','x_mpx',2500),200000)
    def test_expected_value_before_track(self):
        r=change_track(self.r,keyframes=(Keyframe(300,40000),Keyframe(2000,200000)));self.assertEqual(expected_value(r,'standard','marker','x_mpx',0),40000)
    def test_absent_channel_not_invented(self):self.assertIsNone(expected_value(self.r,'standard','marker','rotation_mdeg',1000))
    def test_fractional_frame_clock(self):
        r=replace(self.r,modes=(replace(self.r.modes[0],fps=FrameRate(30000,1001)),));p=replace(self.p,modes=r.modes)
        c=synthetic_capture(self.root,r,p);q=self.check(replace(r,captures=(c,)),p);self.assertNotIn('ANI_CAPTURE_CLOCK_OR_ORDER',codes(q))
