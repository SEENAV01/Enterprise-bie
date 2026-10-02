"""Actual Edge/TCP control-plane journeys; provider calls remain NOT_RUN."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch003d(unittest.TestCase):
    def test_desktop_actual_admin_and_governed_recovery(self):native.NativeUi.journey(self,'desktop',batch003d=True)
    def test_phone_admin_safe_state_and_layout(self):native.NativeUi.journey(self,'phone',batch003d=True)
    def test_tablet_keyboard_and_delayed_private_admin(self):native.NativeUi.journey(self,'tablet',batch003d=True)
if __name__=='__main__':unittest.main(verbosity=2)
