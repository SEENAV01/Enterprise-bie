import unittest
from bie.audio.common import AudioError
from bie.audio.f04_gate import evaluate_f04,validate_f04_gate
from tests.audio.h10_test_support import dir_receipt,compiler,invalidation,rendered

class F04GateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=dir_receipt();cls.c,cls.files=compiler();cls.i=invalidation();cls.r,cls.media,_=rendered();cls.g=evaluate_f04(dir_receipt=cls.d,compiler_receipt=cls.c,compiler_files=cls.files,invalidation_receipt=cls.i,render_receipt=cls.r,render_bytes=cls.media)
    def test_01_gate_implemented(self):self.assertEqual(self.g['implementation_side_status'],'IMPLEMENTED_FOCUSED_TESTED')
    def test_02_dir_bound(self):self.assertEqual(self.g['dir_handoff_fingerprint'],self.d['fingerprint'])
    def test_03_compiler_bound(self):self.assertEqual(self.g['compiler_handoff_fingerprint'],self.c['fingerprint'])
    def test_04_invalidation_bound(self):self.assertEqual(self.g['invalidation_fingerprint'],self.i['fingerprint'])
    def test_05_render_bound(self):self.assertEqual(self.g['technical_render_fingerprint'],self.r['fingerprint'])
    def test_06_real_ffmpeg_is_true(self):self.assertTrue(self.g['real_ffmpeg_av_render_verified'])
    def test_07_real_remotion_is_false(self):self.assertFalse(self.g['real_remotion_render_verified'])
    def test_08_full_regression_still_open(self):self.assertFalse(self.g['full_audio_regression_completed'])
    def test_09_section_exit_still_false(self):self.assertFalse(self.g['section_exit_permitted'])
    def test_10_gate_tamper_fails(self):
        bad=dict(self.g);bad['section_exit_permitted']=True
        with self.assertRaisesRegex(AudioError,'F04_GATE_BOUNDARY'):validate_f04_gate(bad)
    def test_11_gate_self_validates(self):self.assertEqual(validate_f04_gate(self.g),self.g)
    def test_12_no_product_acceptance(self):self.assertFalse(self.g['product_accepted'])
if __name__=='__main__':unittest.main()
