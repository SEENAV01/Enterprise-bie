from .math_contracts import *

def animate_equation_morph(ctx, *, morph_id, source_expression, target_expression,
                           token_map, source_ref, equivalence_status,
                           preserve_unmapped_tokens=True):
    morph_id=tok(morph_id,"morph_id")
    source_expression=tok(source_expression,"source_expression")
    target_expression=tok(target_expression,"target_expression")
    if source_ref not in ctx.evidence_refs:
        raise MathGroundingError("equation morph source_ref not grounded")
    if equivalence_status not in {"equivalent","implication","not_equivalent","unknown"}:
        raise MathEquivalenceError("invalid equivalence_status")
    mapping=dict(token_map or {})
    if not mapping:
        return make_plan(ctx,suffix=":equation-morph",kind="equation_morph",status="BLOCKED",
                         blockers=("semantic_token_map_required",))
    if len(set(mapping.values()))!=len(mapping.values()):
        return make_plan(ctx,suffix=":equation-morph",kind="equation_morph",status="BLOCKED",
                         blockers=("token_map_must_be_one_to_one",))
    if equivalence_status in {"not_equivalent","unknown"}:
        return make_plan(ctx,suffix=":equation-morph",kind="equation_morph",status="BLOCKED",
                         blockers=("equation_morph_requires_equivalence_or_implication",))
    warnings=[]
    if equivalence_status=="implication":
        warnings.append("morph_represents_implication_not_bidirectional_equivalence")
    if not preserve_unmapped_tokens:
        warnings.append("unmapped_tokens_require_explicit_disappearance_semantics")
    ops=(
        {"op":"equation_morph","morph_id":morph_id,"source_expression":source_expression,
         "target_expression":target_expression,"token_map":mapping,
         "equivalence_status":equivalence_status,"preserve_unmapped_tokens":bool(preserve_unmapped_tokens)},
    )
    return make_plan(ctx,suffix=":equation-morph",kind="equation_morph",
                     status="REVIEW" if warnings or ctx.uncertainty>=.4 else "PASS",
                     operations=ops,warnings=warnings)
