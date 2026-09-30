"""METRIC-004: finite forward Horn-rule proofs with trusted premises.

Only valid preceding derivations can serve as premises. Unsupported assertions,
forward/circular references and candidate flags never establish a conclusion.
"""
from ..models import BenchmarkError,ident
from ..domains.structured import record
from .common import ids,indexed,unit,weight

def measure(reference,candidate,artifacts):
    record(reference, {'facts','rules','goals'});record(candidate, {'steps'})
    facts=indexed(reference['facts'],{'id','atom'},lower=1)
    rules=indexed(reference['rules'],{'id','antecedents','consequent'},lower=1)
    goals=indexed(reference['goals'],{'id','atom','weight'},lower=1)
    proven={k:ident(r['atom']) for k,r in facts.items()}
    for row in rules.values():ids(row['antecedents'],lower=1);ident(row['consequent'])
    for row in goals.values():weight(row);ident(row['atom'])
    steps=indexed(candidate['steps'],{'id','rule_id','premises','conclusion'})
    if set(steps)&set(facts):raise BenchmarkError('STEP_SHADOWS_TRUSTED_PREMISE')
    defects=[];valid=[]
    for key,row in steps.items():
        rule_id=ident(row['rule_id']);premises=ids(row['premises']);conclusion=ident(row['conclusion']);reasons=[]
        if rule_id not in rules:reasons.append('UNLICENSED_RULE')
        else:
            rule=rules[rule_id]
            if any(p not in proven for p in premises):reasons.append('UNPROVED_OR_FORWARD_PREMISE')
            elif set(proven[p] for p in premises)!=set(rule['antecedents']):reasons.append('RULE_ANTECEDENTS_MISMATCH')
            if conclusion!=rule['consequent']:reasons.append('RULE_CONCLUSION_MISMATCH')
        if reasons: defects.extend({'id':key,'reason':r} for r in reasons)
        else:proven[key]=conclusion;valid.append(key)
    available=set(proven.values());units=[]
    for key,row in sorted(goals.items()):
        ok=row['atom'] in available
        units.append(unit(key,weight(row),1 if ok else 0,[] if ok else ['GOAL_NOT_DERIVED']))
    return units,defects,{'assessment_scope':'FINITE_HORN_RULE_DERIVATIONS_ONLY','valid_step_ids':valid,
                         'general_reasoning_judgment':False}
