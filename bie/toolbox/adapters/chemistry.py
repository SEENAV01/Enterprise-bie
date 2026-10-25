"""Chemistry computed in Python (RDKit, Cantera) for BIE's web blocks (Task 046a).

- ``molecule``: a molecule from SMILES with 3D coordinates (RDKit ETKDG + MMFF), its formula and an MDL molblock that
  3Dmol.js draws.
- ``reaction``: a reaction applied by RDKit from reaction SMARTS, with 2D drawings (SVG) of every reactant and product
  and an atom-balance check.
- ``kinetics``: how the amounts of species change over time in a reacting gas (Cantera, GRI-Mech 3.0), for a chart.
"""
from __future__ import annotations

from collections import Counter

from .base import clean, need


def _svg(mol, width: int = 360, height: int = 260) -> str:
    from rdkit.Chem.Draw import rdMolDraw2D
    drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
    options = drawer.drawOptions()
    options.clearBackground = False
    options.setBackgroundColour((0, 0, 0, 0))
    options.setSymbolColour((0.95, 0.96, 0.97, 1))
    options.setAtomPalette({-1: (0.95, 0.96, 0.97)})
    options.bondLineWidth = 3
    options.fixedFontSize = 30
    rdMolDraw2D.PrepareAndDrawMolecule(drawer, mol)
    drawer.FinishDrawing()
    return drawer.GetDrawingText()


def molecule(smiles: str, *, name: str = "", seed: int = 7) -> dict:
    need("rdkit")
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdMolDescriptors
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError(f"RDKit cannot read the SMILES {smiles!r}")
    mol = Chem.AddHs(mol)
    params = AllChem.ETKDGv3()
    params.randomSeed = seed
    if AllChem.EmbedMolecule(mol, params) != 0:
        raise ValueError(f"RDKit could not place {smiles!r} in 3D")
    AllChem.MMFFOptimizeMolecule(mol, maxIters=500)
    conf = mol.GetConformer()
    atoms = [{"el": a.GetSymbol(), "x": conf.GetAtomPosition(i).x, "y": conf.GetAtomPosition(i).y, "z": conf.GetAtomPosition(i).z}
             for i, a in enumerate(mol.GetAtoms())]
    bonds = [[b.GetBeginAtomIdx(), b.GetEndAtomIdx(), b.GetBondTypeAsDouble()] for b in mol.GetBonds()]
    return clean({"name": name, "smiles": smiles, "formula": rdMolDescriptors.CalcMolFormula(mol), "atoms": atoms, "bonds": bonds,
                  "molblock": Chem.MolToMolBlock(mol), "computed_by": "rdkit ETKDGv3 + MMFF"}, 3)


def _atoms(mols) -> Counter:
    from rdkit import Chem
    total = Counter()
    for mol in mols:
        for atom in Chem.AddHs(mol).GetAtoms():
            total[atom.GetSymbol()] += 1
    return total


def reaction(smarts: str, reactants: list, *, names: dict | None = None) -> dict:
    """Apply an atom-mapped reaction SMARTS to ``reactants`` (SMILES, one per template, in order). Every reactant and
    product gets its name (``names``: canonical SMILES → name), formula and a 2D drawing; ``balanced`` = the same atoms
    on both sides, counted with hydrogens."""
    need("rdkit")
    from rdkit import Chem
    from rdkit.Chem import AllChem, rdMolDescriptors
    rxn = AllChem.ReactionFromSmarts(smarts)
    mols = [Chem.MolFromSmiles(s) for s in reactants]
    if any(m is None for m in mols):
        raise ValueError("RDKit cannot read a reactant SMILES")
    outcomes = rxn.RunReactants(tuple(mols))
    if not outcomes:
        raise ValueError("the reaction SMARTS does not apply to these reactants")
    products = []
    for p in outcomes[0]:
        Chem.SanitizeMol(p)
        products.append(Chem.MolFromSmiles(Chem.MolToSmiles(p)))
    canon = {Chem.MolToSmiles(Chem.MolFromSmiles(k)): v for k, v in (names or {}).items()}

    def card(mol):
        smi = Chem.MolToSmiles(mol)
        return {"smiles": smi, "name": canon.get(smi, ""), "formula": rdMolDescriptors.CalcMolFormula(mol), "svg": _svg(mol)}
    left, right = _atoms(mols), _atoms(products)
    return {"reactants": [card(m) for m in mols], "products": [card(m) for m in products], "balanced": left == right,
            "atoms_left": dict(sorted(left.items())), "atoms_right": dict(sorted(right.items())),
            "computed_by": "rdkit ReactionFromSmarts + rdMolDraw2D"}


def kinetics(*, fuel: str = "H2", temperature: float = 1100.0, pressure_atm: float = 1.0, phi: float = 1.0, t_end: float = 0.0006,
             points: int = 120, species=("H2", "O2", "H2O", "OH", "H")) -> dict:
    ct = need("cantera")
    np = need("numpy")
    gas = ct.Solution("gri30.yaml")
    gas.TP = temperature, pressure_atm * ct.one_atm
    gas.set_equivalence_ratio(phi, fuel, "O2:1.0")
    reactor = ct.IdealGasReactor(gas)
    net = ct.ReactorNet([reactor])
    times = np.linspace(0.0, t_end, points)
    rows = {s: [] for s in species}
    temps = []
    for t in times:
        if t > 0:
            net.advance(t)
        temps.append(reactor.T)
        for s in species:
            rows[s].append(float(reactor.thermo[s].X[0]))
    return clean({"t_ms": times * 1000.0, "species": rows, "T": temps, "fuel": fuel, "start_K": temperature, "pressure_atm": pressure_atm,
                  "mechanism": "gri30.yaml", "computed_by": f"cantera {ct.__version__} IdealGasReactor"}, 5)
