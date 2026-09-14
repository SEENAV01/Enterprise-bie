"""Emit the truthful offline state for the provider-calibration boundary."""
from dataclasses import asdict
import argparse,hashlib,json,sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from bie.director.director_benchmark import CandidateIdentity
from bie.director.provider_calibration import ProviderStackIdentity,planned_calibration
from bie.director.semantic_execution import EvaluatorIdentity
from examples.director_benchmark import load_suite


def identity():
    files=sorted((ROOT/'bie/director').glob('*.py'))
    code=json.dumps([(p.name,hashlib.sha256(p.read_bytes()).hexdigest()) for p in files],separators=(',',':')).encode()
    candidate=CandidateIdentity('bie-production-director','batch-014',
        'sha256:'+hashlib.sha256(code).hexdigest(),'sha256:'+hashlib.sha256(b'EXTERNAL_PROVIDER_NOT_CONFIGURED').hexdigest())
    return ProviderStackIdentity(
        EvaluatorIdentity('not-configured','generator','not-run'),EvaluatorIdentity('not-configured','critic','not-run'),
        EvaluatorIdentity('not-configured','annotator','not-run'),EvaluatorIdentity('not-configured','reviewer','not-run'),
        candidate,'CONTROLLED_PROTOCOL','NOT_CONFIGURED')


def run():
    suite,sources=load_suite();report=planned_calibration('BIE-DIR-CALIBRATION-PLANNED-001',suite,sources,identity(),
        'No external provider credentials, independent expert-signed corpus, real PDFs or learner study were supplied in this build environment.')
    return {**asdict(report),'eligible_for_acceptance_review':report.eligible_for_acceptance_review,
        'accepted':report.accepted,'report_fingerprint':report.fingerprint(),
        'real_pdf_executed':False,'live_provider_executed':False,'rendered_media_executed':False,
        'playable_game_executed':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path);args=parser.parse_args();result=run()
    if args.output:args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({key:result[key] for key in ('status','eligible_for_acceptance_review','accepted','report_fingerprint')}))
