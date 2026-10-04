"""Actual inherited assertions over the genuine POSIX producer plus live mutant."""
from pathlib import Path
import importlib.util,unittest
from unittest.mock import patch
from bie.compiler import chromium_resource_worker as worker
ROOT=Path(__file__).resolve().parents[2]
class KernelCallerControls(unittest.TestCase):
 def authored_cases(self):
  for filename,cls,method in [('test_comp_h7_007.py','IntegratedProductionGateTests','test_kernel_producer_not_bridge'),
                            ('test_comp_h8_005.py','ActualProducerAdoptionTests','test_real_producer_keeps_kernel_policy')]:
   spec=importlib.util.spec_from_file_location('caller_control_'+filename.replace('.','_'),ROOT/'tests/compiler'/filename)
   module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
   yield getattr(module,cls)(method),method
 def test_actual_callers_accept_genuine_scoped_kernel_driver(self):
  for case,method in self.authored_cases():getattr(case,method)()
 def test_actual_callers_reject_seeded_non_kernel_driver(self):
  def non_kernel(config):return None
  for case,method in self.authored_cases():
   with patch.object(worker,'_driver',non_kernel):self.assertRaises(AssertionError,getattr(case,method))
if __name__=='__main__':unittest.main(verbosity=2)
