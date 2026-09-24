import unittest,shutil
from bie.audio.common import AudioError
from bie.audio.render_evidence import validate_render_receipt
from tests.audio.h10_test_support import rendered

@unittest.skipUnless(shutil.which('ffmpeg') and shutil.which('ffprobe'),'ffmpeg required')
class RenderEvidenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.r,cls.data,cls.root=rendered()
    def test_01_real_ffmpeg_run(self):self.assertTrue(self.r['real_ffmpeg_av_render_verified'])
    def test_02_has_video(self):self.assertIn('video',self.r['stream_types'])
    def test_03_has_audio(self):self.assertIn('audio',self.r['stream_types'])
    def test_04_has_caption_stream(self):self.assertIn('subtitle',self.r['stream_types'])
    def test_05_nonempty_mp4(self):self.assertGreater(len(self.data),1000)
    def test_06_receipt_validates(self):self.assertEqual(validate_render_receipt(self.r,self.data),self.r)
    def test_07_tampered_bytes_fail(self):
        with self.assertRaisesRegex(AudioError,'TECHNICAL_RENDER_BYTES'):validate_render_receipt(self.r,self.data+b'x')
    def test_08_not_remotion(self):self.assertFalse(self.r['real_remotion_render_verified'])
    def test_09_not_human_listening(self):self.assertFalse(self.r['human_listening_verified'])
    def test_10_not_product_acceptance(self):self.assertFalse(self.r['product_accepted'])
if __name__=='__main__':unittest.main()
