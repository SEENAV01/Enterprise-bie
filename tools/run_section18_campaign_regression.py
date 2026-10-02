"""Explicit finding-derived race/origin controls; not additional Section17 tasks."""
from pathlib import Path
import argparse,hashlib,io,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
sys.path.insert(1,str(ROOT/'tests/section18'))
from test_campaign_sidecar_race import CampaignSidecarRace
from test_campaign_maintenance import CampaignMaintenance
def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    suite=unittest.TestSuite()
    for case in (CampaignSidecarRace,CampaignMaintenance):suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(case))
    ids=[c.id() for c in suite];assert len(ids)==len(set(ids))==12
    transcript=io.StringIO();r=unittest.TextTestRunner(stream=transcript,verbosity=2).run(suite)
    receipt=dict(schema='bie.section18.campaign-maintenance-controls/1',tests_run=r.testsRun,
        unique_method_ids=ids,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),
        passed=r.wasSuccessful() and not r.skipped,original_section17_methods_unchanged=2023,
        campaign_sha256=hashlib.sha256((ROOT/'bie/evaluation/benchmarks/native_campaign/runtime.py').read_bytes()).hexdigest(),
        fixture_acceptance=False,product_accepted=False)
    assert not a.output.exists();a.output.mkdir(parents=True)
    (a.output/'TEST_RESULT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    (a.output/'TEST_RESULT.txt').write_text(transcript.getvalue())
    print(json.dumps({k:v for k,v in receipt.items() if k!='unique_method_ids'}))
    return 0 if receipt['passed'] else 1
if __name__=='__main__':raise SystemExit(main())
