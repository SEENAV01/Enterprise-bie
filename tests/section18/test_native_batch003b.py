"""Real TCP/Edge native ledger dashboards, phone/tablet and stale-read control."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch003b(unittest.TestCase):
    def test_desktop_native_benchmark_release_and_lineage(self):native.NativeUi.journey(self,'desktop',batch003b=True)
    def test_phone_structured_quality_and_access_clear(self):native.NativeUi.journey(self,'phone',batch003b=True)
    def test_tablet_quality_keyboard_and_stale_read(self):native.NativeUi.journey(self,'tablet',batch003b=True)
if __name__=='__main__':unittest.main(verbosity=2)
