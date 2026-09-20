from __future__ import annotations

import re
from typing import Any, Mapping, Sequence
from .grammar_contracts import VisualGrammar, GrammarValidationError, finite_number, make_plan

CHEMISTRY_MOLECULAR_GRAMMAR = VisualGrammar(
    grammar_id="bie.vis.grammar.chemistry_molecular", version="1.0.0",
    domains=("chemistry",), representations=("molecule", "reaction_structure"),
    allowed_primitives=("atom", "bond", "charge_label", "lone_pair", "reaction_arrow", "label"),
    required_roles=("atom",),
    semantic_constraints=("bond order is explicit", "formal charge is preserved when supplied", "2D depiction does not imply stereochemistry unless stereochemistry is explicitly encoded"),
    aliases=("chemistry-molecular",), tags=("atom", "bond", "molecule"),
)
_ELEMENT = re.compile(r"^[A-Z][a-z]?$|^D$|^T$")


def plan_molecule(atoms: Sequence[Mapping[str, Any]], bonds: Sequence[Mapping[str, Any]], *, evidence_refs: Sequence[str], reasoning_refs: Sequence[str], stereochemistry_explicit: bool = False):
    elements, ids = [], set()
    for atom in atoms:
        aid = str(atom.get("id", "")).strip(); symbol = str(atom.get("element", "")).strip()
        if not aid or aid in ids: raise GrammarValidationError("atom ids must be non-blank and unique")
        if not _ELEMENT.match(symbol): raise GrammarValidationError(f"invalid element symbol syntax: {symbol}")
        ids.add(aid)
        charge = atom.get("formal_charge", 0)
        if isinstance(charge, bool) or not isinstance(charge, int): raise GrammarValidationError("formal_charge must be an integer")
        elements.append({"id": f"atom:{aid}", "role": "atom", "primitive": "atom", "label": str(atom.get("label", symbol)), "source_ids": list(atom.get("source_ids", evidence_refs)), "payload": {"element": symbol, "formal_charge": charge, "isotope": atom.get("isotope")}})
    if not elements: raise GrammarValidationError("at least one atom is required")
    relations = []
    for i, bond in enumerate(bonds):
        src, dst = str(bond.get("source", "")).strip(), str(bond.get("target", "")).strip()
        if src not in ids or dst not in ids or src == dst: raise GrammarValidationError("bond endpoints must be distinct known atoms")
        order = finite_number(bond.get("order", 1), field_name="bond.order")
        if order not in {1.0, 1.5, 2.0, 3.0}: raise GrammarValidationError("bond order must be 1, 1.5, 2, or 3")
        relations.append({"id": f"bond:{i}:{src}:{dst}", "source": f"atom:{src}", "target": f"atom:{dst}", "kind": "bond", "source_ids": list(bond.get("source_ids", evidence_refs)), "payload": {"order": order, "stereo": bond.get("stereo") if stereochemistry_explicit else None}})
    warnings = [] if stereochemistry_explicit else ["stereochemistry is not implied by the 2D molecular layout"]
    return make_plan(CHEMISTRY_MOLECULAR_GRAMMAR, evidence_refs=evidence_refs, reasoning_refs=reasoning_refs, elements=elements, relations=relations, constraints=CHEMISTRY_MOLECULAR_GRAMMAR.semantic_constraints, warnings=warnings)
