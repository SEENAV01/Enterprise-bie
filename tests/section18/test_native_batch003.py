"""Actual HTTP video decode + isolated native-compiled synthetic game journeys."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch003(unittest.TestCase):
    def test_desktop_media_decode_game_interaction_and_revocation(self):native.NativeUi.journey(self,'desktop',batch003=True)
    def test_phone_preview_accessibility_and_clear(self):native.NativeUi.journey(self,'phone',batch003=True)
    def test_tablet_preview_accessibility_and_clear(self):native.NativeUi.journey(self,'tablet',batch003=True)
if __name__=='__main__':unittest.main(verbosity=2)
