"""Actual native browser executions; synthetic artifacts stay labelled."""
import sys, unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import test_native_ui as native
class NativeBatch002(unittest.TestCase):
    def test_desktop_all_viewers_lineage_evidence_and_literal_code(self):native.NativeUi.journey(self,'desktop',True)
    def test_phone_structured_viewers_and_accessibility(self):native.NativeUi.journey(self,'phone',True)
    def test_tablet_structured_viewers_and_accessibility(self):native.NativeUi.journey(self,'tablet',True)
if __name__=='__main__':unittest.main(verbosity=2)
