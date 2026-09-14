from dataclasses import dataclass
@dataclass(frozen=True)
class SocraticStep: kind:str; prompt:str; target_concept:str; evidence_ids:tuple[str,...]
def socratic_sequence(target_concept,claim,evidence_ids,misconception=None):
    if not target_concept.strip() or not claim.strip() or not evidence_ids: raise ValueError("grounding")
    ev=tuple(sorted(set(evidence_ids))); out=[SocraticStep("ELICIT",f"What do you think about: {claim}?",target_concept,ev)]
    if misconception: out.append(SocraticStep("CHALLENGE",f"What evidence would challenge this idea: {misconception}?",target_concept,ev))
    out.extend([SocraticStep("PROBE","What evidence supports your answer?",target_concept,ev),SocraticStep("CONNECT","How does this connect to what we already established?",target_concept,ev),SocraticStep("REFINE","Can you state the idea more precisely now?",target_concept,ev)])
    return tuple(out)
