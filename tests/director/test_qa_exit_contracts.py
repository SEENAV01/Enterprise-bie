"""DIR QA-006/007 boundary regressions with preserved SYNC consumers."""
from dataclasses import replace
import unittest
from pacing_fixtures import timed, beat, evaluate
from qa_fixtures import codes
from bie.director.pause_timing import build_pause_timing, PauseCue
from bie.director.scene_duration_fit import fit_scene_durations
from bie.director.pacing_qa import validate_pacing_report
from bie.director.sync_contract import build_sync_context


class ExitContractTests(unittest.TestCase):
    def test_reflection_repair_preserves_source_and_rebuilds_sync_context(self):
        c=timed(); original_script=c.snapshot.fingerprint(); beats=(beat(c,minimum=2000),)
        report=evaluate(c,beats); sync=build_sync_context(c.speech,c.pauses,c.emphasis)
        c.pauses=build_pause_timing(c.speech,(PauseCue('reflect','u1',6,2000,'Process this explanation',('e1',)),))
        c.timeline=fit_scene_durations(c.speech,c.pauses,c.emphasis)
        repaired=evaluate(c,beats); resync=build_sync_context(c.speech,c.pauses,c.emphasis)
        self.assertIn('REQUIRED_REFLECTION_SHORTFALL',codes(report))
        self.assertNotIn('REQUIRED_REFLECTION_SHORTFALL',codes(repaired))
        self.assertEqual(c.snapshot.fingerprint(),original_script)
        self.assertNotEqual(sync.fingerprint(),resync.fingerprint())
        with self.assertRaises(ValueError): validate_pacing_report(report,c.snapshot,c.speech,c.pauses,c.emphasis,c.timeline,beats)

    def test_wpm_edit_preserves_text_but_invalidates_pacing_and_sync(self):
        c=timed(); changed=timed(wpm=180)
        report=evaluate(c,(beat(c),))
        self.assertEqual(c.snapshot,changed.snapshot)
        with self.assertRaises(ValueError): validate_pacing_report(report,changed.snapshot,changed.speech,changed.pauses,changed.emphasis,changed.timeline,(beat(changed),))
        self.assertNotEqual(build_sync_context(c.speech,c.pauses,c.emphasis).fingerprint(),build_sync_context(changed.speech,changed.pauses,changed.emphasis).fingerprint())

    def test_scene_boundaries_do_not_reset_continuous_speech_measurement(self):
        texts=tuple(' '.join(['concept']*60) for _ in range(3))
        c=timed(texts,scene_ids=('first','second','third'))
        r=evaluate(c,tuple(beat(c,u.utterance_id) for u in c.snapshot.utterances))
        self.assertEqual(dict(r.measurements)['longest_continuous_speech_ms'],72000)
        self.assertIn('CONTINUOUS_SPEECH_REVIEW',codes(r))


if __name__=='__main__': unittest.main()
