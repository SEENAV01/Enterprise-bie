from dataclasses import dataclass
import re

class ChemistryAnimationError(ValueError): pass

@dataclass(frozen=True)
class Species:
    species_id:str
    formula:str
    coefficient:int
    source_refs:tuple[str,...]
    reasoning_refs:tuple[str,...]
    phase:str|None=None
    charge:int|None=None

@dataclass(frozen=True)
class ChemistryPlan:
    reaction_id:str
    status:str
    reactants:tuple[Species,...]
    products:tuple[Species,...]
    conserved_atoms:bool
    charge_balanced:bool|None
    operations:tuple[dict,...]
    blockers:tuple[str,...]
    warnings:tuple[str,...]
    review_required:bool=True
    accepted:bool=False

_atom_pat=re.compile(r"([A-Z][a-z]?)(\d*)")

def _atoms(formula):
    out={}
    for sym,n in _atom_pat.findall(formula):
        out[sym]=out.get(sym,0)+(int(n) if n else 1)
    if not out: raise ChemistryAnimationError("formula parse failed")
    return out

def _totals(species):
    total={}
    for s in species:
        if s.coefficient<1: raise ChemistryAnimationError("coefficient must be positive")
        for atom,n in _atoms(s.formula).items():
            total[atom]=total.get(atom,0)+n*s.coefficient
    return total

def plan_reaction(reaction_id,reactants,products,*,reaction_kind="transformation",show_bond_changes=False,
                  model_generated=False,model_fingerprint=None):
    reactants=tuple(reactants);products=tuple(products)
    if not reactants or not products: raise ChemistryAnimationError("reactants/products required")
    if any(not s.source_refs or not s.reasoning_refs for s in reactants+products):
        raise ChemistryAnimationError("species lineage required")
    blockers=[];warnings=[]
    conserved=_totals(reactants)==_totals(products)
    if not conserved: blockers.append("atom_conservation_failed")
    charges=[s.charge for s in reactants+products]
    charge_balanced=None
    if all(c is not None for c in charges):
        left=sum(s.coefficient*s.charge for s in reactants)
        right=sum(s.coefficient*s.charge for s in products)
        charge_balanced=left==right
        if not charge_balanced: blockers.append("charge_conservation_failed")
    elif any(c is not None for c in charges):
        warnings.append("partial_charge_information")
    if show_bond_changes and reaction_kind not in {"transformation","substitution","addition","elimination","redox"}:
        warnings.append("bond_change_animation_requires_review_for_reaction_kind")
    if model_generated and not model_fingerprint:
        blockers.append("model_generated_chemistry_requires_model_fingerprint")
    ops=(
      {"op":"materialize_species","reactants":[s.__dict__ for s in reactants],"products":[s.__dict__ for s in products]},
      {"op":"animate_reaction","reaction_kind":reaction_kind,"show_bond_changes":bool(show_bond_changes),
       "model_generated":bool(model_generated)}
    )
    status="BLOCKED" if blockers else ("REVIEW" if warnings else "PASS")
    return ChemistryPlan(reaction_id,status,reactants,products,conserved,charge_balanced,ops,
                         tuple(sorted(set(blockers))),tuple(sorted(set(warnings))),True,False)
