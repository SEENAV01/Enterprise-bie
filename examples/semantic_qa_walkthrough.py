"""Execute the semantic QA integration with deterministic protocol fixtures.

The provider below tests execution/binding/retry behavior only. Its fixed verdict
is deliberately labelled as a fixture and never trusted by the default policy.
Run live calibrated providers separately through the same ModelProvider contract.
"""
from dataclasses import asdict
import argparse,json
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from examples.director_benchmark import load_suite,controlled_director
from bie.director.semantic_execution import evaluate_script_semantics,EvaluatorIdentity
from bie.model_gateway.model_interface import ModelResponse


class ProtocolFixtureCritic:
    def __init__(self): self.calls=0
    def invoke(self,request):
        self.calls+=1; payload=json.loads(request.messages[1]['content'])
        if self.calls==1:
            content='deliberately malformed fixture response'
        else:
            content={name:payload[name] for name in ('claim_id','claim_fingerprint','passage_fingerprints')}
            content.update(verdict='SUPPORTED',confidence=.95,rationale='Fixture verdict for protocol testing only; not semantic evidence.')
        return ModelResponse('protocol-fixture','critic',content,{},'completed',{'fixture':True})


def run():
    suite,sources=load_suite(); case=suite.cases[0]; output=controlled_director(case.request)
    provider=ProtocolFixtureCritic()
    source_ids={p.source_id for p in case.request.catalog.pages}
    result=evaluate_script_semantics(output.snapshot,output.claims,case.request.catalog,
        tuple(s for s in sources if s.source_id in source_ids),provider,EvaluatorIdentity('protocol-fixture','critic','adapter/1'))
    return {'scope':'Actual semantic-executor invocation using a deterministic protocol fixture; no live model accuracy measurement',
        'provider_calls':provider.calls,'status':result.status,'accepted':result.accepted,'live_model_executed':False,
        'real_book_executed':False,'result_fingerprint':result.fingerprint(),'evaluation':asdict(result)}


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--output',type=Path); args=parser.parse_args(); result=run()
    if args.output:
        args.output.parent.mkdir(parents=True,exist_ok=True); args.output.write_text(json.dumps(result,indent=2,ensure_ascii=False)+'\n')
        print(json.dumps({k:result[k] for k in ('provider_calls','status','accepted','live_model_executed','result_fingerprint')}))
    else: print(json.dumps(result,indent=2,ensure_ascii=False))
