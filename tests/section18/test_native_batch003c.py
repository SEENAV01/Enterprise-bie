"""Actual Edge/TCP QA dashboard; no synthetic repair-history substitution."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch003c(unittest.TestCase):
    def test_desktop_native_gate_and_missing_repair(self):native.NativeUi.journey(self,'desktop',batch003c=True)
    def test_phone_canonical_gates_and_access_clear(self):native.NativeUi.journey(self,'phone',batch003c=True)
    def test_tablet_keyboard_and_held_assurance_response(self):native.NativeUi.journey(self,'tablet',batch003c=True)
if __name__=='__main__':unittest.main(verbosity=2)
