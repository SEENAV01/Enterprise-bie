from dir_helpers import *
from fractions import Fraction

class ScriptPacing(FixtureCase):
    def test_technical_term_missing_introduction(self):
        self.assertCode(self.run_check(replace(self.request,term_introductions=())),'script','DIR_TERM_USED_BEFORE_EXPLANATION')
    def test_technical_term_late_introduction(self):
        r=replace(self.request,term_introductions=(replace(self.request.term_introductions[0],beat_id='b-payoff'),))
        self.assertCode(self.run_check(r),'script','DIR_TERM_USED_BEFORE_EXPLANATION')
    def test_term_intro_requires_actual_term(self):
        r=replace(self.request,term_introductions=(replace(self.request.term_introductions[0],beat_id='b-transition'),))
        self.assertCode(self.run_check(r),'script','DIR_TERM_INTRO_NOT_EXPLANATORY')
    def test_unknown_term(self):
        r=replace(self.request,term_introductions=(replace(self.request.term_introductions[0],term_id='unknown'),))
        self.assertCode(self.run_check(r),'script','DIR_TERM_INTRO_REFERENCE')
    def test_operator_assumed_knowledge_is_explicit(self):
        p=replace(self.policy,terms=(replace(self.policy.terms[0],assumed_known=True),))
        self.assertEqual(self.run_check(replace(self.request,term_introductions=()),p).status,'CHECKS_PASSED')
    def test_todo_in_actual_text(self):
        r,p,c=fixture(self.root,source_overrides={'c-recap':'[TODO] Write the recap.'})
        self.assertCode(self.run_check(r,p),'script','DIR_UNRESOLVED_PLACEHOLDER')
    def test_template_in_actual_text(self):
        r,p,c=fixture(self.root,source_overrides={'c-recap':'Recap {{concept_name}} now.'})
        self.assertCode(self.run_check(r,p),'script','DIR_UNRESOLVED_PLACEHOLDER')
    def test_hidden_override(self):
        r,p,c=fixture(self.root,source_overrides={'c-recap':'Recap \u202e concealed text.'})
        self.assertCode(self.run_check(r,p),'script','DIR_HIDDEN_OR_INVALID_TEXT')
    def test_voice_drift(self):
        self.assertCode(self.run_check(self.beat('b-example',voice_id='unexpected-voice')),'script','DIR_SPEAKER_VOICE_DRIFT')
    def test_second_declared_speaker_allowed(self):
        self.assertEqual(self.run_check(self.beat('b-example',speaker_id='student',voice_id='student-voice')).status,'CHECKS_PASSED')
    def test_long_sentence_is_review_not_reading_score(self):
        x=self.run_check(p=self.limit(max_sentence_codepoints=10))
        self.assertCode(x,'script','DIR_SENTENCE_GUARDRAIL','REVIEW_REQUIRED')
    def test_duplicate_text_not_new_explanation(self):
        extra=Beat('repeat','s2','explanation','narration',20000,30000,('c-example',),('obj-count',))
        r=replace(self.request,beats=self.request.beats+(extra,))
        self.assertCode(self.run_check(r),'script','DIR_UNJUSTIFIED_REPETITION')
    def test_justified_recap_reference(self):
        r=self.beat('b-recap',claim_ids=('c-recap','c-example'),repeat_of=('b-example',))
        self.assertNotIn('DIR_REPEAT_TARGET_INVALID',codes(self.run_check(r).script))
    def test_future_recap_reference(self):
        self.assertCode(self.run_check(self.beat('b-hook',repeat_of=('b-example',))),'script','DIR_REPEAT_TARGET_INVALID')
    def test_exact_recap_reuse_can_pass(self):
        # Preserve the separate recap text as well; the duplicate event has a justified role.
        extra=Beat('repeat','s2','recap','narration',30000,40000,('c-example',),('obj-count',),repeat_of=('b-example',))
        r=replace(self.request,scenes=change(self.request.scenes,'scene_id','s2',duration_ms=40000),beats=self.request.beats+(extra,))
        p=replace(self.policy,routes=(replace(self.policy.routes[0],max_duration_ms=75000),))
        self.assertEqual(self.run_check(r,p).status,'CHECKS_PASSED')
    def test_speech_overflow(self):
        self.assertCode(self.run_check(self.beat('b-example',end_ms=31000)),'pacing','DIR_BEAT_OVERFLOW')
    def test_speech_too_fast(self):
        self.assertCode(self.run_check(self.beat('b-example',end_ms=17001)),'pacing','DIR_SPEECH_RATE_EXCEEDED')
    def test_overlapping_voices(self):
        self.assertCode(self.run_check(self.beat('b-example',start_ms=16000)),'pacing','DIR_OVERLAPPING_SPEECH')
    def test_touching_boundaries_not_overlap(self):
        self.assertNotIn('DIR_OVERLAPPING_SPEECH',codes(self.run_check().pacing))
    def test_pause_has_no_speech(self):
        self.assertCode(self.run_check(self.beat('b-example',end_ms=28000)),'pacing','DIR_PAUSE_OCCUPIED_BY_SPEECH')
    def test_pause_budget(self):
        self.assertCode(self.run_check(p=self.limit(max_pause_ms=1000)),'pacing','DIR_PAUSE_TOO_LONG')
    def test_missing_time_not_averaged_away(self):
        self.assertCode(self.run_check(self.beat('b-example',start_ms=26000)),'pacing','DIR_UNMOTIVATED_GAP')
    def test_leading_gap(self):
        self.assertCode(self.run_check(self.beat('b-hook',start_ms=4500),self.limit(max_unmotivated_gap_ms=4000)),'pacing','DIR_UNMOTIVATED_GAP')
    def test_trailing_gap(self):
        self.assertCode(self.run_check(self.beat('b-recap',end_ms=24000)),'pacing','DIR_UNMOTIVATED_GAP')
    def test_route_duration_budget(self):
        p=replace(self.policy,routes=(replace(self.policy.routes[0],max_duration_ms=59999),))
        self.assertCode(self.run_check(p=p),'pacing','DIR_ROUTE_DURATION')
    def test_reflection_time_floor(self):
        p=replace(self.policy,timing_constraints=(replace(self.policy.timing_constraints[0],minimum_gap_ms=4000),))
        self.assertCode(self.run_check(p=p),'pacing','DIR_TIMING_CONSTRAINT')
    def test_timing_endpoint_cannot_disappear(self):
        p=replace(self.policy,timing_constraints=(replace(self.policy.timing_constraints[0],before_beat_id='absent'),))
        self.assertCode(self.run_check(p=p),'pacing','DIR_TIMING_ENDPOINT_MISSING')
    def test_equation_needs_expanded_readout(self):
        r,p,c=fixture(self.root,source_overrides={'c-example':'Two groups of three: 2 * 3 = 6.'})
        self.assertCode(self.run_check(r,p),'pacing','DIR_MATH_READOUT_REQUIRED','REVIEW_REQUIRED')
    def test_equation_expanded_readout(self):
        r,p,c=fixture(self.root,source_overrides={'c-example':'Two groups of three: 2 * 3 = 6.'})
        r,p,c=with_readout(self.root,r,p,c,'Two multiplied by three equals six counters.')
        self.assertEqual(self.run_check(r,p).status,'CHECKS_PASSED')
    def test_short_readout_cannot_hide_overflow(self):
        r=self.beat('b-example',end_ms=17500);r=replace(r,spoken_forms=(SpokenForm('b-example','one'),))
        result=self.run_check(r)
        self.assertTrue(any(f.code=='DIR_SPEECH_RATE_EXCEEDED' and f.subject_id=='b-example' for f in result.pacing.findings))
    def test_long_readout_is_counted(self):
        r=replace(self.request,spoken_forms=(SpokenForm('b-example','An extremely long explanation. '*500),))
        self.assertCode(self.run_check(r),'pacing','DIR_SPEECH_RATE_EXCEEDED')
    def test_unknown_spoken_form(self):
        self.assertCode(self.run_check(replace(self.request,spoken_forms=(SpokenForm('absent','Text'),))),'pacing','DIR_SPOKEN_FORM_ORPHAN')
    def test_spoken_placeholder(self):
        self.assertCode(self.run_check(replace(self.request,spoken_forms=(SpokenForm('b-example','[TODO]'),))),'script','DIR_UNRESOLVED_SPOKEN_PLACEHOLDER')
    def test_spoken_control(self):
        self.assertCode(self.run_check(replace(self.request,spoken_forms=(SpokenForm('b-example','\u202ehidden'),))),'script','DIR_HIDDEN_OR_INVALID_SPOKEN_TEXT')
    def screen_request(self):
        src=replace(self.request.source,outputs=(replace(self.request.source.outputs[0],channel='on_screen'),))
        return replace(self.request,source=src,beats=tuple(replace(b,channel='on_screen') if b.channel!='pause' else b for b in self.request.beats))
    def test_screen_rate_measured(self):
        r=self.screen_request();self.assertEqual(self.run_check(r).status,'CHECKS_PASSED')
        self.assertGreater(dict(self.run_check(r).pacing.measurements)['max_screen_codepoints_per_minute_ceil'],0)
    def test_screen_too_fast(self):
        r=self.screen_request();r=replace(r,beats=change(r.beats,'beat_id','b-example',end_ms=17010))
        self.assertCode(self.run_check(r),'pacing','DIR_SCREEN_RATE_EXCEEDED')
    def test_concurrent_screen_rate(self):
        r=self.screen_request()
        r=replace(r,beats=change(r.beats,'beat_id','b-example',start_ms=10000,end_ms=20000))
        # Both streams fit individually under 600, but their overlap does not.
        self.assertCode(self.run_check(r,self.limit(screen_codepoints_per_minute=600)),'pacing','DIR_CONCURRENT_SCREEN_RATE')
    def test_concurrent_speech_rate_even_when_count_allowed(self):
        r=self.beat('b-example',start_ms=10000,end_ms=20000)
        self.assertCode(self.run_check(r,self.limit(speech_codepoints_per_minute=800,max_concurrent_speech=2)),'pacing','DIR_CONCURRENT_SPEECH_RATE')

    def test_metadata_readout_not_enough(self):
        r=replace(self.request,spoken_forms=(SpokenForm('b-example','Two multiplied by three equals six counters.'),))
        self.assertCode(self.run_check(r),'script','DIR_SPOKEN_FORM_UNGROUNDED','REVIEW_REQUIRED')
    def test_readout_actual_bytes_checked(self):
        r,p,c=with_readout(self.root,self.request,self.policy,self.candidate,'Two multiplied by three equals six counters.')
        (self.root/'outputs/expanded-readout.txt').write_text('altered')
        self.assertEqual(self.run_check(r,p).status,'BLOCKED')
    def test_readout_span_mismatch_blocks(self):
        r,p,c=with_readout(self.root,self.request,self.policy,self.candidate,'Two multiplied by three equals six counters.')
        r=replace(r,spoken_forms=(replace(r.spoken_forms[0],text='one'),))
        self.assertCode(self.run_check(r,p),'script','DIR_SPOKEN_FORM_TEXT_MISMATCH')
    def test_readout_requires_own_fidelity_mapping(self):
        r,p,c=with_readout(self.root,self.request,self.policy,self.candidate,'Two multiplied by three equals six counters.')
        r=replace(r,fidelity=r.fidelity[:-1])
        self.assertCode(self.run_check(r,p),'fidelity','DIR_FIDELITY_SCOPE_MISMATCH')
    def test_unknown_readout_claim(self):
        r=replace(self.request,spoken_forms=(SpokenForm('b-example','Speech',('unknown',)),))
        self.assertCode(self.run_check(r),'script','DIR_SPOKEN_FORM_EVIDENCE_INVALID')
    def test_readout_cannot_hide_unexplained_term(self):
        r,p,c=with_readout(self.root,self.request,self.policy,self.candidate,'The product is six counters.')
        p=replace(p,terms=p.terms+(TermRequirement('term-product',('product',)),))
        self.assertCode(self.run_check(r,p),'script','DIR_TERM_USED_BEFORE_EXPLANATION')
