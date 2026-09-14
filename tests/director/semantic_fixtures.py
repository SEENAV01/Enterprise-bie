"""Protocol fixtures only; no semantic model quality or live calls implied."""
from dataclasses import replace
import json
from bie.director.semantic_execution import EvaluatorIdentity,SemanticExecutionPolicy,evaluator_key,evaluate_script_semantics
from bie.director.factual_script_qa import FactualPolicy
from bie.director.source_grounding_qa import SourceBytes
from bie.model_gateway.model_interface import ModelResponse

IDENTITY=EvaluatorIdentity('protocol-fixture','critic','adapter/1')


def trusted_policy(identity=IDENTITY,**changes):
    p=SemanticExecutionPolicy(**changes)
    return replace(p,factual_policy=FactualPolicy(trusted_evaluators=(evaluator_key(identity,p),)))


def response_record(payload,**changes):
    data={k:payload[k] for k in ('claim_id','claim_fingerprint','passage_fingerprints')}
    data.update(verdict='SUPPORTED',confidence=.95,rationale='Controlled protocol verdict; not empirical semantic evidence.')
    data.update(changes); return data


class ProtocolFixtureProvider:
    def __init__(self,transform=None,identity=IDENTITY): self.requests=[]; self.transform=transform; self.identity=identity
    def invoke(self,request):
        self.requests.append(request)
        payload=json.loads(request.messages[1]['content'])
        content=self.transform(payload,len(self.requests)) if self.transform else response_record(payload)
        return ModelResponse(self.identity.provider,self.identity.model,content,{},'completed',{'test_fixture':True})


def artifacts(c): return tuple(SourceBytes(s,d,'text/plain; charset=utf-8') for s,d in c.source_data)


def evaluate(c,provider=None,identity=IDENTITY,policy=None):
    provider=provider or ProtocolFixtureProvider(identity=identity)
    return evaluate_script_semantics(c.snapshot,c.claims,c.catalog,artifacts(c),provider,identity,policy or trusted_policy(identity))
