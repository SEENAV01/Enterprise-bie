"""Real sandbox-enabled Edge DOM/TCP governance journeys."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch004(unittest.TestCase):
    def test_desktop_actual_policy_activation_and_audit(self):native.NativeUi.journey(self,'desktop',batch004=True)
    def test_phone_frozen_benchmark_config_and_safe_layout(self):native.NativeUi.journey(self,'phone',batch004=True)
    def test_tablet_credential_clear_discards_delayed_audit(self):native.NativeUi.journey(self,'tablet',batch004=True)
if __name__=='__main__':unittest.main(verbosity=2)
