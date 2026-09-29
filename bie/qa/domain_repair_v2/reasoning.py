"""Rebuild bounded deductive support chains from EXISTING reviewed propositions.

No added root premise, changed conclusion, new scientific assumption or live model.
Formal entailment is not factual truth or validation of natural-language mapping.
"""
from dataclasses import replace
from ..release_v2.contracts import ContractError
from ..reasoning_v2.models import ReasoningRequest,ReasoningPolicy
from ..reasoning_v2.logic import entailment
from .contracts import Limits
from .common import exact_inputs,finish

def repair(request,root,policy,limits=Limits()):
    if type(request) is not ReasoningRequest or type(policy) is not ReasoningPolicy:raise ContractError('DOMAIN_REPAIR_REASONING_TYPE')
    exact_inputs(request,root)
    if set(policy.expected_argument_ids)!={a.argument_id for a in request.arguments}:raise ContractError('DOMAIN_REPAIR_ARGUMENT_SCOPE')
    statements={s.statement_id:s for s in request.statements};steps={s.step_id:s for s in request.steps}
    owners={};calls=0;visits=0;witnesses=[];new_steps=dict(steps);arguments=[]
    def proof(premises,conclusion):
        nonlocal calls,visits
        calls+=1
        if calls>limits.max_proof_calls:raise ContractError('DOMAIN_REPAIR_PROOF_BUDGET')
        if not 1<=len(premises)<=64:raise ContractError('DOMAIN_REPAIR_PROOF_WIDTH')
        exprs=tuple(statements[p].expression for p in premises)
        conclusion_expr=statements[conclusion].expression
        atoms={a for e in exprs+(conclusion_expr,) for a in e.atoms}
        if len(atoms)>policy.max_proof_atoms:raise ContractError('DOMAIN_REPAIR_LOGIC_RESOURCE_LIMIT')
        cost=(1<<len(atoms))*sum(e.node_count for e in exprs+(conclusion_expr,))
        visits+=cost
        if visits>limits.max_total_logic_visits:raise ContractError('DOMAIN_REPAIR_TOTAL_LOGIC_BUDGET')
        result=entailment(exprs,conclusion_expr,max_atoms=policy.max_proof_atoms,
            max_assignments=policy.max_truth_assignments,max_node_visits=policy.max_node_visits)
        if result.status=='RESOURCE_LIMIT':raise ContractError('DOMAIN_REPAIR_LOGIC_RESOURCE_LIMIT')
        if result.status=='INCONSISTENT_PREMISES':raise ContractError('DOMAIN_REPAIR_INCONSISTENT_PREMISES')
        return result
    for arg in request.arguments:
        if any(s not in statements or statements[s].scope!=arg.scope for s in arg.statement_ids):raise ContractError('DOMAIN_REPAIR_LOGICAL_SCOPE')
        if not set(arg.premise_ids+(arg.conclusion_id,))<=set(arg.statement_ids):raise ContractError('DOMAIN_REPAIR_LOGICAL_REFERENCE')
        if any(s not in steps for s in arg.step_ids):raise ContractError('DOMAIN_REPAIR_MISSING_STEP')
        conclusion_ids=[steps[s].conclusion_id for s in arg.step_ids]
        if len(set(conclusion_ids))!=len(conclusion_ids) or set(conclusion_ids)&set(arg.premise_ids):raise ContractError('DOMAIN_REPAIR_MULTIPLE_OR_ROOT_CONCLUSION')
        if not set(conclusion_ids)<=set(arg.statement_ids) or arg.conclusion_id not in conclusion_ids:raise ContractError('DOMAIN_REPAIR_CONCLUSION_MISSING')
        for sid in arg.step_ids:
            if sid in owners:raise ContractError('DOMAIN_REPAIR_SHARED_STEP_UNSUPPORTED')
            owners[sid]=arg.argument_id
            if steps[sid].method!='deductive':raise ContractError('DOMAIN_REPAIR_NONDEDUCTIVE_REVIEW_REQUIRED')
        # Check the complete root set, so contradictory roots cannot be hidden by
        # choosing a conveniently consistent subset during reconstruction.
        root_check=proof(arg.premise_ids,arg.conclusion_id)
        if root_check.status!='ENTAILED':raise ContractError('DOMAIN_REPAIR_CONCLUSION_NOT_ENTAILED')
        available=list(arg.premise_ids);remaining=list(arg.step_ids);order=[]
        while remaining:
            progress=False
            for sid in tuple(remaining):
                step=steps[sid];result=proof(tuple(available),step.conclusion_id)
                if result.status!='ENTAILED':continue
                new_steps[sid]=replace(step,premise_ids=tuple(available))
                witnesses.append(dict(argument_id=arg.argument_id,step_id=sid,premise_ids=list(available),
                    conclusion_id=step.conclusion_id,formal_status=result.status,assignments_checked=result.assignments_checked))
                available.append(step.conclusion_id);remaining.remove(sid);order.append(sid);progress=True
            if not progress:raise ContractError('DOMAIN_REPAIR_INTERMEDIATE_NOT_ENTAILED')
        arguments.append(replace(arg,step_ids=tuple(order)))
    if set(steps)!=set(owners):raise ContractError('DOMAIN_REPAIR_UNASSIGNED_STEP')
    after=replace(request,steps=tuple(new_steps[s.step_id] for s in request.steps),arguments=tuple(arguments))
    return finish(request,after,dict(worker='bounded-deductive-chain-reconstruction',proof_calls=calls,conservative_node_visits=visits,steps=witnesses,
        premise_truth_verified=False,root_premises_changed=False,conclusions_changed=False,
        assumptions_changed=False,calibration_changed=False),limits)
