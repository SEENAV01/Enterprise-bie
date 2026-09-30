#!/usr/bin/env python3
"""Deliberately corrupt trusted reference behavior in memory to test detection.

These are fault-sensitivity controls, not native BIE runs or extra passed tests.
No source file is modified. A control succeeds only if the unmodified named test
passes AND the injected behavior makes the same test fail AND the restored test
passes again. Unexpected errors are not counted as detected assertion failures.
"""
from __future__ import annotations
import argparse,importlib,io,json,sys,unittest
from contextlib import nullcontext
from fractions import Fraction
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT),str(ROOT/'tests/section17'),str(ROOT/'tools')];sys.dont_write_bytecode=True
from run_section17_tests import inventory
from bie.evaluation.benchmarks.domains import photosynthesis,physiology,genetics,bonding,stoichiometry,temporal,plate_tectonics,historical_causality

def run_one(name,context):
    stream=io.StringIO()
    with context:
        suite=unittest.defaultTestLoader.loadTestsFromName(name)
        result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
    return {'tests_run':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'skips':len(result.skipped),'success':result.wasSuccessful(),'log':stream.getvalue()}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output-dir',required=True);a=p.parse_args();out=Path(a.output_dir);out.mkdir(parents=True,exist_ok=False)
    controls=[
        ('photosynthesis_wrong_oxygen_source','test_bio_001.BIO001Tests.test_authored_case_008',lambda:patch.dict(photosynthesis.PROFILE,oxygen_source='carbon_dioxide')),
        ('genetics_collapsed_distribution','test_bio_002.BIO002Tests.test_four_loci_cartesian_distribution',lambda:patch.object(genetics,'locus_cross',lambda item:{item['gene']*2:Fraction(1)})),
        ('physiology_litre_conversion_dropped','test_bio_003.BIO003Tests.test_frequency_and_volume_unit_equivalence',lambda:patch.dict(physiology.VOLUME,L=1)),
        ('bonding_lone_pairs_ignored','test_chem_001.CHEM001Tests.test_all_supported_vsepr_shapes',lambda:patch.dict(bonding.GEOMETRIES,{(2,2):('tetrahedral','tetrahedral')})),
        ('stoichiometry_conservation_bypassed','test_chem_003.CHEM003Tests.test_authored_case_011',lambda:patch.object(stoichiometry,'conserved',lambda *args:True)),
        ('historical_sequence_always_prior','test_hist_002.HIST002Tests.test_same_day_does_not_imply_prior_cause',lambda:patch.object(historical_causality,'relation',lambda *args:'BEFORE')),
        ('chronology_invented_year_zero','test_hist_003.HIST003Tests.test_one_bce_to_one_ce_consecutive_days',lambda:patch.object(temporal,'astronomical_year',lambda y,e:y if e=='CE' else -y)),
        ('geology_mm_conversion_dropped','test_geo_001.GEO001Tests.test_mm_and_cm_rate_equivalence',lambda:patch.dict(plate_tectonics.RATES,{'mm/yr':1})),
    ]
    before=inventory();records=[]
    for key,test,make_patch in controls:
        baseline=run_one(test,nullcontext());mutated=run_one(test,make_patch());restored=run_one(test,nullcontext())
        detected=baseline['success'] and restored['success'] and mutated['failures']>0 and mutated['errors']==0 and mutated['skips']==0
        records.append({'control_id':key,'test_id':test,'detected':detected,'baseline':baseline,'injected':mutated,'restored':restored})
    changed=before!=inventory()
    body={'scope':'IN_MEMORY_REFERENCE_FAULT_SENSITIVITY_ONLY','controls':records,'controls_count':len(records),'controls_detected':sum(r['detected'] for r in records),'source_changed':changed,'all_detected':all(r['detected'] for r in records) and not changed,'native_bie_run':False,'product_accepted':False,'counting_note':'Repeated named test runs here are not added to the distinct unittest count.'}
    (out/'FAULT_CONTROLS.json').write_text(json.dumps(body,indent=2)+'\n')
    print(json.dumps({k:body[k] for k in ('controls_count','controls_detected','source_changed','all_detected')}));return 0 if body['all_detected'] else 1
if __name__=='__main__':raise SystemExit(main())
