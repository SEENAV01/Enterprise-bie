"""Proof-graph and exact bounded deduction checks. Non-deductive steps need review."""
from dataclasses import dataclass,asdict
from ..release_v2.contracts import ContractError
from .logic import entailment

@dataclass(frozen=True, slots=True)
class ProofWitness:
    argument_id: str
    step_id: str
    status: str
    assignments_required: int
    assignments_checked: int
    witness: tuple[tuple[str,bool],...]


def check_proofs(c):
    r,p=c.request,c.policy;witnesses=[];valid=set();invalid=set();required_total=0;checked_total=0;node_budget=p.max_node_visits
    def run(aid,sid,premises,conclusion):
        nonlocal required_total,checked_total,node_budget
        atoms={atom for f in premises+(conclusion,) for atom in f.atoms}
        required=(1<<len(atoms)) if len(atoms)<=p.max_proof_atoms else 0
        nodes=required*sum(f.node_count for f in premises+(conclusion,))
        remaining=p.max_truth_assignments-required_total
        if required==0 or remaining<1 or nodes>node_budget:
            status='RESOURCE_LIMIT';checked=0;witness=()
        else:
            result=entailment(premises,conclusion,max_atoms=p.max_proof_atoms,max_assignments=remaining,max_node_visits=max(1,node_budget))
            status=result.status;checked=result.assignments_checked;witness=result.witness
        required_total+=required;checked_total+=checked;node_budget=max(0,node_budget-nodes)
        witnesses.append(ProofWitness(aid,sid,status,required,checked,witness))
        if status!='ENTAILED':
            c.add('validity',{'COUNTEREXAMPLE':'REASONING_COUNTEREXAMPLE','INCONSISTENT_PREMISES':'INCONSISTENT_ROOT_PREMISES','RESOURCE_LIMIT':'PROOF_BUDGET_EXCEEDED'}[status],aid,
                  f'{sid}: {status}. No truncated proof or inconsistent-premise explosion may be accepted.')
        return status=='ENTAILED'
    if set(c.arguments)!=set(p.expected_argument_ids):
        c.add('validity','ARGUMENT_INVENTORY_MISMATCH','reasoning-scope','Submitted arguments must exactly match the independently provisioned inventory.')
    used_statements=set();used_steps=set()
    for a in sorted(r.arguments,key=lambda x:x.argument_id):
        aid=a.argument_id;used_statements.update(a.statement_ids);used_steps.update(a.step_ids)
        before=len(c.findings['validity'])
        if (not set(a.statement_ids)<=set(c.statements) or not set(a.step_ids)<=set(c.steps) or
            not set(a.premise_ids)<=set(a.statement_ids) or a.conclusion_id not in a.statement_ids):
            c.add('validity','ARGUMENT_REFERENCE_MISSING',aid,'Argument refers to missing statements, steps, root premises or conclusion.');invalid.add(aid);continue
        ss={i:c.statements[i] for i in a.statement_ids};steps=[c.steps[i] for i in a.step_ids]
        if any(s.scope!=a.scope for s in ss.values()):c.add('validity','LOGICAL_CONTEXT_MISMATCH',aid,'Proof atoms cannot be combined across different declared scopes.')
        if any(s.claim_id not in c.claims for s in ss.values()):c.add('validity','LOGICAL_CLAIM_MISSING',aid,'Every statement must bind an actual output claim.')
        if any(s.claim_id in c.claims and c.claims[s.claim_id].kind!='FACT' and sid not in a.assumption_ids for sid,s in ss.items()):c.add('validity','LOGICAL_STATEMENT_NOT_FACTUAL',aid,'A nonfactual output label cannot hide an asserted premise or conclusion.')
        if a.assumption_ids and a.conclusion_mode!='conditional':c.add('validity','UNDISCLOSED_ASSUMPTIONS',aid,'Assumptions may support only an explicitly conditional conclusion.')
        if a.conclusion_mode=='conditional' and ('disclosure',aid) not in c.ready:
            c.add('validity','CONDITIONAL_DISCLOSURE_UNVERIFIED',aid,'An authenticated output review must verify that conditions are visible.','REVIEW')
        producers={};bad=False
        for st in steps:
            if st.conclusion_id in producers or st.conclusion_id in a.premise_ids:
                c.add('validity','DUPLICATE_OR_ROOT_PROOF_PRODUCER',aid,'A root premise cannot also be derived; each conclusion has one producer.');bad=True
            if st.conclusion_id not in ss or not set(st.premise_ids)<=set(ss):
                c.add('validity','STEP_REFERENCE_MISSING',st.step_id,'Step escapes the argument statement inventory.');bad=True
            producers[st.conclusion_id]=st
        if a.conclusion_id not in producers:c.add('validity','CONCLUSION_HAS_NO_PRODUCER',aid,'A final conclusion needs an explicit inference step.');bad=True
        if bad:invalid.add(aid);continue
        # All declared material must participate in the final proof cone.
        pending=[a.conclusion_id];cone=set()
        while pending:
            sid=pending.pop()
            if sid in cone:continue
            cone.add(sid)
            if sid in producers:pending.extend(producers[sid].premise_ids)
        if cone!=set(ss):c.add('validity','IRRELEVANT_PROOF_MATERIAL',aid,'Unused premises, claims or conclusions cannot pad a proof/evidence inventory.')
        if set(ss)!=set(a.premise_ids)|set(producers):c.add('validity','UNJUSTIFIED_PROOF_STATEMENT',aid,'Every statement must be either a declared root or the conclusion of a step.')
        if any(f.severity=='BLOCKER' for f in c.findings['validity'][before:]):invalid.add(aid);continue
        # Global consistency: local valid steps must not hide contradictory roots.
        roots=tuple(ss[i].expression for i in a.premise_ids)
        good=run(aid,'root-consistency',roots,roots[0])
        available=set(a.premise_ids);todo={st.step_id:st for st in steps}
        while todo:
            eligible=sorted(k for k,st in todo.items() if set(st.premise_ids)<=available)
            if not eligible:
                c.add('validity','PROOF_CYCLE_OR_UNRESOLVED_DEPENDENCY',aid,'No remaining step has an acyclic justified premise path.');good=False;break
            for sid in eligible:
                st=todo.pop(sid)
                if st.method=='deductive':
                    passed=run(aid,sid,tuple(ss[i].expression for i in st.premise_ids),ss[st.conclusion_id].expression)
                else:
                    passed=('inference',st.step_id) in c.ready
                    witnesses.append(ProofWitness(aid,sid,'REVIEWED_NONDEDUCTIVE' if passed else 'NONDEDUCTIVE_REVIEW_REQUIRED',0,0,()))
                    if not passed:c.add('validity','NONDEDUCTIVE_INFERENCE_UNVERIFIED',sid,'A causal/inductive/analogical/empirical label is not a logical or evidential warrant.','REVIEW')
                good=good and passed
                # Still traverse dependent structure to expose further invalid steps;
                # a failed predecessor cannot be turned into overall validity.
                available.add(st.conclusion_id)
        if ('mapping',aid) not in c.ready:
            c.add('validity','PROOF_TEXT_MAPPING_UNVERIFIED',aid,'Formal entailment cannot establish that these formulas faithfully represent the output.','REVIEW');good=False
        if good and not any(f.severity!='INFO' for f in c.findings['validity'][before:]):valid.add(aid)
        if any(f.severity=='BLOCKER' for f in c.findings['validity'][before:]):invalid.add(aid)
    if used_statements!=set(c.statements):c.add('validity','ORPHAN_LOGICAL_STATEMENTS','reasoning-scope','Unassigned statements are not excluded silently from reasoning QA.')
    if used_steps!=set(c.steps):c.add('validity','ORPHAN_INFERENCE_STEPS','reasoning-scope','Unassigned steps are not excluded silently from reasoning QA.')
    c.metrics['validity'].update(arguments=len(r.arguments),verified_arguments=len(valid),
        assignments_required=required_total,assignments_checked=checked_total,proof_witnesses=len(witnesses))
    return tuple(witnesses),valid,invalid
