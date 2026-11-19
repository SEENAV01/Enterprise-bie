"""Reaction mechanisms for the PYQ lab (Navin, 19 November 2026): electron-pair arrows applied to real molecules.

The maker writes a mechanism as short lines over atom-mapped SMILES; RDKit (BSD-3-Clause) holds the molecules and this
module applies each curved arrow as a change of bonds and formal charges, then checks what chemistry demands:

  * a lone-pair arrow starts on an atom that has a lone pair; a bond arrow starts on a bond that exists;
  * after every step every atom has a valence RDKit accepts, and atoms, electrons and total charge are conserved
    (by construction: each arrow moves one pair);
  * a 1,2-shift really is 1,2 and makes a more stable carbocation; and when a carbocation could become more stable by
    one 1,2-shift that the mechanism does not make, the check says so (a rearrangement is never forced, never missed);
  * the product, compared as a canonical structure, decides which option is right, and a trap path's product shows
    which wrong option it explains.

    reactant [CH3:1][CH:2]([OH:6])[C:3]([H:9])([CH3:4])[CH3:5]
    reactant [H:7][Br:8]
    label 2 C2
    step s1 protonation: lp 6 -> 7; bond 7-8 -> 8
    step s2 water leaves: bond 2-6 -> 6
    step s3 hydride shift: shift 9 3 -> 2
    step s4 bromide attacks: lp 8 -> 3
    trap t1 after s2 direct swap at C2: lp 8 -> 2
    option 2 CCC(C)(C)Br

Arrows: ``lp D -> A`` (a lone pair of D makes a new D–A bond), ``bond A-B -> B`` (the A–B pair goes to B; the bond
breaks or loses one order), ``shift G A -> B`` (group G moves from A to the next atom B with its bond pair), ``pi A-B ->
B-C`` (the A–B pair becomes a B–C bond). Each arrow moves exactly two electrons.
"""
from __future__ import annotations

import math
import re

VALENCE_E = {"H": 1, "B": 3, "C": 4, "N": 5, "O": 6, "F": 7, "Si": 4, "P": 5, "S": 6, "Cl": 7, "Br": 7, "I": 7}
DEGREE_WORD = {0: "methyl", 1: "1°", 2: "2°", 3: "3°"}
ARROW = re.compile(r"^\s*(?:lp\s+(\d+)\s*->\s*(\d+)|bond\s+(\d+)\s*-\s*(\d+)\s*->\s*(\d+)|"
                   r"shift\s+(\d+)\s+(\d+)\s*->\s*(\d+)|pi\s+(\d+)\s*-\s*(\d+)\s*->\s*(\d+)\s*-\s*(\d+))\s*$")
STEP = re.compile(r"^\s*step\s+([a-z][a-z0-9_]*)\s+([^:]*):\s*(.+)$", re.I)
TRAP = re.compile(r"^\s*trap\s+([a-z][a-z0-9_]*)\s+after\s+([a-z][a-z0-9_]*)\s+([^:]*):\s*(.+)$", re.I)


class ChemProblem(ValueError):
    pass


def available() -> bool:
    try:
        from rdkit import RDLogger
        RDLogger.DisableLog("rdApp.*")          # problems are reported by this module, in words
        return True
    except ImportError:
        return False


def parse(lines: list) -> tuple:
    spec = {"reactants": [], "labels": {}, "steps": [], "traps": [], "options": {}}
    problems = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        word = line.split()[0].lower()
        try:
            if word == "reactant":
                spec["reactants"].append(line.split(None, 1)[1].strip())
            elif word == "label":
                _, num, tag = line.split(None, 2)
                spec["labels"][int(num)] = tag.strip()
            elif word == "step":
                m = STEP.match(line)
                if not m:
                    raise ChemProblem("write 'step <id> <what happens>: <arrow>; <arrow>'")
                spec["steps"].append({"id": m.group(1), "label": m.group(2).strip(), "arrows": arrows(m.group(3))})
            elif word == "trap":
                m = TRAP.match(line)
                if not m:
                    raise ChemProblem("write 'trap <id> after <step id or start> <what the student does>: <arrows>'")
                spec["traps"].append({"id": m.group(1), "after": m.group(2), "label": m.group(3).strip(),
                                      "arrows": arrows(m.group(4))})
            elif word == "option":
                _, num, smiles = (line.split(None, 2) + [""])[:3]
                spec["options"][int(num) - 1] = "" if smiles.strip().lower() in ("", "none", "-") else smiles.strip()
            else:
                raise ChemProblem("lines start with reactant, label, step, trap or option")
        except (ChemProblem, ValueError, IndexError) as exc:
            problems.append(f"mechanism line {line!r}: {exc}")
    if not spec["reactants"]:
        problems.append("mechanism: no 'reactant' line")
    if not spec["steps"]:
        problems.append("mechanism: no 'step' line")
    ids = [s["id"] for s in spec["steps"]] + [t["id"] for t in spec["traps"]]
    if len(ids) != len(set(ids)):
        problems.append("mechanism: step and trap ids must be different")
    return spec, problems


def arrows(text: str) -> list:
    out = []
    for part in [p for p in text.split(";") if p.strip()]:
        m = ARROW.match(part)
        if not m:
            raise ChemProblem(f"arrow {part.strip()!r} not understood (lp D -> A | bond A-B -> B | shift G A -> B | "
                              f"pi A-B -> B-C)")
        g = m.groups()
        if g[0]:
            out.append({"kind": "lp", "src": [int(g[0])], "dst": [int(g[1])]})
        elif g[2]:
            if int(g[4]) not in (int(g[2]), int(g[3])):
                raise ChemProblem("a bond arrow ends on one of the bond's own atoms")
            out.append({"kind": "bond", "src": [int(g[2]), int(g[3])], "dst": [int(g[4])]})
        elif g[5]:
            out.append({"kind": "shift", "src": [int(g[5]), int(g[6])], "dst": [int(g[7])]})
        else:
            if int(g[9]) != int(g[10]):
                raise ChemProblem("a pi arrow keeps one atom: pi A-B -> B-C")
            out.append({"kind": "pi", "src": [int(g[8]), int(g[9])], "dst": [int(g[10]), int(g[11])]})
    return out


class Mech:
    """The reacting system: one RDKit molecule (all hydrogens explicit) whose bonds and charges the arrows change."""

    def __init__(self, reactants: list, labels: dict):
        from rdkit import Chem
        params = Chem.SmilesParserParams()
        params.removeHs = False
        mol = None
        for smiles in reactants:
            part = Chem.MolFromSmiles(smiles, params)
            if part is None:
                raise ChemProblem(f"RDKit cannot read the SMILES {smiles!r}")
            part = Chem.AddHs(part)
            mol = part if mol is None else Chem.CombineMols(mol, part)
        self.mol = Chem.RWMol(mol)
        for atom in self.mol.GetAtoms():
            atom.SetNoImplicit(True)
            atom.SetNumExplicitHs(0)
        self.index = {}
        for atom in self.mol.GetAtoms():
            num = atom.GetAtomMapNum()
            if num:
                if num in self.index:
                    raise ChemProblem(f"atom map number {num} is used twice")
                self.index[num] = atom.GetIdx()
        self.labels = labels
        self.reactant_count = len(reactants)

    def idx(self, num: int) -> int:
        if num not in self.index:
            raise ChemProblem(f"atom {num} has no map number in the reactants (map every atom an arrow touches)")
        return self.index[num]

    def aid(self, i: int) -> str:
        num = self.mol.GetAtomWithIdx(i).GetAtomMapNum()
        return f"a{num}" if num else f"u{i}"

    def name(self, num: int) -> str:
        atom = self.mol.GetAtomWithIdx(self.idx(num))
        return self.labels.get(num) or f"{atom.GetSymbol()}{num}"

    def copy(self) -> "Mech":
        from rdkit import Chem
        other = object.__new__(Mech)
        other.mol, other.index, other.labels, other.reactant_count = Chem.RWMol(self.mol), self.index, self.labels, \
            self.reactant_count
        return other

    def lone_pairs(self, i: int) -> int:
        atom = self.mol.GetAtomWithIdx(i)
        bonds = sum(b.GetBondTypeAsDouble() for b in atom.GetBonds())
        nonbonding = VALENCE_E.get(atom.GetSymbol(), 0) - atom.GetFormalCharge() - bonds
        return max(0, int(nonbonding) // 2)

    def _bond_down(self, a: int, b: int, what: str):
        from rdkit import Chem
        bond = self.mol.GetBondBetweenAtoms(a, b)
        if bond is None:
            raise ChemProblem(f"{what}: there is no bond between {self.aid(a)} and {self.aid(b)}")
        order = bond.GetBondTypeAsDouble()
        if order >= 3:
            bond.SetBondType(Chem.BondType.DOUBLE)
        elif order >= 2:
            bond.SetBondType(Chem.BondType.SINGLE)
        else:
            self.mol.RemoveBond(a, b)

    def _bond_up(self, a: int, b: int):
        from rdkit import Chem
        bond = self.mol.GetBondBetweenAtoms(a, b)
        if bond is None:
            self.mol.AddBond(a, b, Chem.BondType.SINGLE)
        elif bond.GetBondTypeAsDouble() < 2:
            bond.SetBondType(Chem.BondType.DOUBLE)
        else:
            bond.SetBondType(Chem.BondType.TRIPLE)

    def _charge(self, i: int, delta: int):
        atom = self.mol.GetAtomWithIdx(i)
        atom.SetFormalCharge(atom.GetFormalCharge() + delta)

    def apply(self, arrow: dict) -> dict:
        """Apply one arrow; returns what changed (formed/broken bonds as atom ids)."""
        kind = arrow["kind"]
        if kind == "lp":
            d, a = self.idx(arrow["src"][0]), self.idx(arrow["dst"][0])
            if self.lone_pairs(d) < 1:
                raise ChemProblem(f"{self.aid(d)} has no lone pair to give")
            self._bond_up(d, a)
            self._charge(d, +1)
            self._charge(a, -1)
            return {"formed": [[self.aid(d), self.aid(a)]], "broken": [], "donor": self.aid(d), "acceptor": self.aid(a)}
        if kind == "bond":
            x, y = self.idx(arrow["src"][0]), self.idx(arrow["src"][1])
            to = self.idx(arrow["dst"][0])
            other = x if to == y else y
            self._bond_down(x, y, "bond arrow")
            self._charge(other, +1)
            self._charge(to, -1)
            return {"formed": [], "broken": [[self.aid(x), self.aid(y)]], "donor": self.aid(other), "acceptor": self.aid(to)}
        if kind == "shift":
            g, frm, to = self.idx(arrow["src"][0]), self.idx(arrow["src"][1]), self.idx(arrow["dst"][0])
            if self.mol.GetBondBetweenAtoms(frm, to) is None:
                raise ChemProblem(f"shift: {self.aid(frm)} and {self.aid(to)} are not next to each other (a 1,2-shift "
                                  f"moves a group to the neighbouring atom)")
            self._bond_down(g, frm, "shift")
            self._bond_up(to, g)
            self._charge(frm, +1)
            self._charge(to, -1)
            return {"formed": [[self.aid(to), self.aid(g)]], "broken": [[self.aid(frm), self.aid(g)]],
                    "donor": self.aid(frm), "acceptor": self.aid(to), "moved": self.aid(g)}
        a, b = self.idx(arrow["src"][0]), self.idx(arrow["src"][1])
        c = self.idx(arrow["dst"][1])
        self._bond_down(a, b, "pi arrow")
        self._bond_up(b, c)
        self._charge(a, +1)
        self._charge(c, -1)
        return {"formed": [[self.aid(b), self.aid(c)]], "broken": [[self.aid(a), self.aid(b)]], "donor": self.aid(a),
                "acceptor": self.aid(c)}

    def check_valence(self) -> list:
        from rdkit import Chem
        probe = Chem.Mol(self.mol)
        try:
            Chem.SanitizeMol(probe)
        except Exception as exc:               # RDKit names the atom and its valence
            return [f"after this step RDKit refuses the structure: {str(exc).splitlines()[0]}"]
        return []

    def carbocations(self) -> list:
        out = []
        for atom in self.mol.GetAtoms():
            if atom.GetSymbol() == "C" and atom.GetFormalCharge() == 1:
                degree = sum(1 for n in atom.GetNeighbors() if n.GetSymbol() == "C")
                out.append({"atom": self.aid(atom.GetIdx()), "idx": atom.GetIdx(), "degree": degree,
                            "word": DEGREE_WORD.get(degree, f"{degree}°")})
        return out

    def better_shift(self, cation_idx: int) -> dict | None:
        """A 1,2-shift (H or alkyl, from a neighbouring carbon) that would make a more substituted carbocation."""
        atom = self.mol.GetAtomWithIdx(cation_idx)
        degree = sum(1 for n in atom.GetNeighbors() if n.GetSymbol() == "C")
        best = None
        for nb in atom.GetNeighbors():
            if nb.GetSymbol() != "C" or nb.GetFormalCharge() != 0:
                continue
            for group in nb.GetNeighbors():
                if group.GetIdx() == cation_idx or group.GetSymbol() not in ("H", "C"):
                    continue
                new_degree = sum(1 for n in nb.GetNeighbors() if n.GetSymbol() == "C" and n.GetIdx() != group.GetIdx())
                new_degree += 0  # the old cation carbon stays a carbon neighbour of nb
                if new_degree > degree and (best is None or new_degree > best["degree"]):
                    best = {"from": self.aid(nb.GetIdx()), "group": group.GetSymbol(), "degree": new_degree,
                            "word": DEGREE_WORD.get(new_degree, f"{new_degree}°"), "now": DEGREE_WORD.get(degree)}
        return best

    def fragments(self) -> list:
        from rdkit import Chem
        probe = Chem.Mol(self.mol)
        frags = Chem.GetMolFrags(probe, asMols=False, sanitizeFrags=False)
        out = []
        for atoms in frags:
            carbons = sum(1 for i in atoms if self.mol.GetAtomWithIdx(i).GetSymbol() == "C")
            out.append({"atoms": list(atoms), "carbons": carbons, "smiles": fragment_smiles(self.mol, atoms)})
        return out

    def product(self) -> dict:
        frags = self.fragments()
        main = max(frags, key=lambda f: (f["carbons"], len(f["atoms"])))
        others = [f["smiles"] for f in frags if f is not main]
        return {"smiles": main["smiles"], "byproducts": others}

    def state(self) -> dict:
        """Atoms (heavy atoms and mapped hydrogens) and bonds for the player."""
        atoms, shown = [], set()
        for atom in self.mol.GetAtoms():
            if atom.GetSymbol() == "H" and not atom.GetAtomMapNum():
                continue
            shown.add(atom.GetIdx())
        for i in sorted(shown):
            atom = self.mol.GetAtomWithIdx(i)
            hidden_h = sum(1 for n in atom.GetNeighbors() if n.GetSymbol() == "H" and n.GetIdx() not in shown)
            label = atom.GetSymbol() + ("H" if hidden_h == 1 else f"H{hidden_h}" if hidden_h else "")
            num = atom.GetAtomMapNum()
            atoms.append({"id": self.aid(i), "el": atom.GetSymbol(), "label": label, "tag": self.labels.get(num, ""),
                          "charge": atom.GetFormalCharge(), "lp": self.lone_pairs(i) if atom.GetSymbol() != "C" else 0})
        bonds = []
        for bond in self.mol.GetBonds():
            a, b = bond.GetBeginAtomIdx(), bond.GetEndAtomIdx()
            if a in shown and b in shown:
                bonds.append({"a": self.aid(a), "b": self.aid(b), "order": int(bond.GetBondTypeAsDouble())})
        return {"atoms": atoms, "bonds": bonds, "shown": sorted(shown)}


def fragment_smiles(mol, atoms) -> str:
    from rdkit import Chem
    keep = set(atoms)
    piece = Chem.RWMol(mol)
    for i in sorted((a.GetIdx() for a in piece.GetAtoms() if a.GetIdx() not in keep), reverse=True):
        piece.RemoveAtom(i)
    for atom in piece.GetAtoms():
        atom.SetAtomMapNum(0)
    try:
        clean = Chem.RemoveHs(piece.GetMol(), sanitize=True)
        return Chem.MolToSmiles(clean)
    except Exception:
        return Chem.MolToSmiles(piece.GetMol())


def canonical(smiles: str) -> str | None:
    from rdkit import Chem
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    for atom in mol.GetAtoms():
        atom.SetAtomMapNum(0)
    return Chem.MolToSmiles(mol)


def layout(mech: Mech) -> dict:
    """2D positions (bond length 1) of the shown atoms of the reactants, each reactant beside the last."""
    from rdkit import Chem
    from rdkit.Chem import AllChem
    state = mech.state()
    shown = set(state["shown"])
    pos, x_offset = {}, 0.0
    for atoms in Chem.GetMolFrags(Chem.Mol(mech.mol), asMols=False, sanitizeFrags=False):
        keep = [i for i in atoms if i in shown]
        piece = Chem.RWMol(mech.mol)
        for i in sorted((a.GetIdx() for a in piece.GetAtoms() if a.GetIdx() not in keep), reverse=True):
            piece.RemoveAtom(i)
        mol = piece.GetMol()
        mol.UpdatePropertyCache(strict=False)
        AllChem.Compute2DCoords(mol)
        conf = mol.GetConformer()
        pts = [(conf.GetAtomPosition(k).x / 1.5, -conf.GetAtomPosition(k).y / 1.5) for k in range(mol.GetNumAtoms())]
        min_x = min(p[0] for p in pts)
        max_x = max(p[0] for p in pts)
        for k, original in enumerate(keep):
            pos[mech.aid(original)] = [round(pts[k][0] - min_x + x_offset, 3), round(pts[k][1], 3)]
        x_offset += (max_x - min_x) + 2.2
    return pos


def _neighbours(mech: Mech, aid: str) -> list:
    i = _idx_of(mech, aid)
    return [mech.aid(n.GetIdx()) for n in mech.mol.GetAtomWithIdx(i).GetNeighbors()]


def _idx_of(mech: Mech, aid: str) -> int:
    return mech.index[int(aid[1:])] if aid.startswith("a") else int(aid[1:])


def _component(mech: Mech, start: str, blocked: str | None = None) -> set:
    seen, todo = {start}, [start]
    while todo:
        cur = todo.pop()
        for n in _neighbours(mech, cur):
            if n != blocked and n not in seen:
                seen.add(n)
                todo.append(n)
    return seen


def _outward(pos: dict, mech: Mech, aid: str, skip=()) -> tuple:
    me = pos.get(aid, [0, 0])
    others = [pos[n] for n in _neighbours(mech, aid) if n in pos and n not in skip]
    if not others:
        return (1.0, -0.4)
    cx = sum(p[0] for p in others) / len(others)
    cy = sum(p[1] for p in others) / len(others)
    dx, dy = me[0] - cx, me[1] - cy
    length = math.hypot(dx, dy) or 1.0
    return (dx / length, dy / length)


def move_positions(before: Mech, after: Mech, changes: list, pos: dict) -> dict:
    """Where the shown atoms sit after a step: a captured or migrating group comes to its new partner, a leaving group
    moves away. Everything else stays, so the learner sees only what the arrows changed."""
    pos = {k: list(v) for k, v in pos.items()}
    for change in changes:
        for a, b in change.get("formed", []):
            moved = change.get("moved")
            if moved:                                # a 1,2-shift: the group (and what hangs on it) moves to b's side
                anchor, group = a, moved
                piece = _component(after, group, blocked=anchor)
            else:
                comp_a, comp_b = _component(before, a), _component(before, b)
                if comp_a == comp_b:
                    continue
                anchor, group = (a, b) if len(comp_a) >= len(comp_b) else (b, a)
                piece = comp_b if group == b else comp_a
            if anchor not in pos or group not in pos:
                continue
            ox, oy = _outward(pos, after, anchor, skip=piece)
            target = (pos[anchor][0] + ox, pos[anchor][1] + oy)
            dx, dy = target[0] - pos[group][0], target[1] - pos[group][1]
            for atom in piece:
                if atom in pos:
                    pos[atom] = [round(pos[atom][0] + dx, 3), round(pos[atom][1] + dy, 3)]
        for a, b in change.get("broken", []):
            if change.get("moved"):
                continue
            comp_a, comp_b = _component(after, a), _component(after, b)
            if comp_a == comp_b or a not in pos or b not in pos:
                continue
            small, big_atom, small_atom = (comp_b, a, b) if len(comp_b) <= len(comp_a) else (comp_a, b, a)
            dx, dy = pos[small_atom][0] - pos[big_atom][0], pos[small_atom][1] - pos[big_atom][1]
            length = math.hypot(dx, dy) or 1.0
            for atom in small:
                if atom in pos:
                    pos[atom] = [round(pos[atom][0] + dx / length * 1.3, 3), round(pos[atom][1] + dy / length * 1.3, 3)]
    return pos


def run(lines: list, options: list) -> dict:
    """The whole mechanism checked. Returns states for the player, facts per step, the product and option matches."""
    out = {"kind": "mechanism", "problems": [], "states": [], "steps": [], "traps": [], "product": None,
           "answer_option": None, "trap_options": {}, "facts": []}
    if not available():
        out["problems"].append("RDKit is not installed here, so the mechanism cannot be checked (pip install rdkit)")
        return out
    spec, problems = parse(lines)
    out["problems"] += problems
    if problems:
        return out
    try:
        mech = Mech(spec["reactants"], spec["labels"])
    except ChemProblem as exc:
        out["problems"].append(f"mechanism: {exc}")
        return out
    pos = layout(mech)
    out["states"].append({"id": "start", **mech.state(), "pos": pos, "cations": mech.carbocations()})
    snapshots = {"start": (mech.copy(), pos)}
    step_ids = [s["id"] for s in spec["steps"]]
    for n, step in enumerate(spec["steps"]):
        before = mech.copy()
        changes = []
        try:
            for arrow in step["arrows"]:
                changes.append(mech.apply(arrow))
        except ChemProblem as exc:
            out["problems"].append(f"step {step['id']} ({step['label']}): {exc}")
            return out
        found = mech.check_valence()
        if found:
            out["problems"] += [f"step {step['id']} ({step['label']}): {p}" for p in found]
            return out
        cations = mech.carbocations()
        before_cations = {c["atom"]: c for c in before.carbocations()}
        facts = []
        for change, arrow in zip(changes, step["arrows"]):
            if arrow["kind"] == "shift":
                old = before_cations.get(change["acceptor"])
                new = next((c for c in cations if c["atom"] == change["donor"]), None)
                if old and new and new["degree"] <= old["degree"]:
                    out["problems"].append(f"step {step['id']}: this shift turns a {old['word']} carbocation into a "
                                           f"{new['word']} one; a 1,2-shift happens only when it gives a more stable "
                                           f"carbocation")
                if old and new:
                    facts.append(f"{old['word']} → {new['word']} carbocation")
        nxt = spec["steps"][n + 1] if n + 1 < len(spec["steps"]) else None
        for cat in cations:
            better = mech.better_shift(cat["idx"])
            shifts_next = nxt and any(a["kind"] == "shift" for a in nxt["arrows"])
            if better and not shifts_next:
                out["problems"].append(f"after step {step['id']} the {cat['word']} carbocation at {cat['atom']} could "
                                       f"become {better['word']} by a 1,2-shift of {better['group']} from "
                                       f"{better['from']}; show that shift, or the mechanism misses the major product")
        pos = move_positions(before, mech, changes, pos)
        out["states"].append({"id": step["id"], **mech.state(), "pos": pos, "cations": cations})
        out["steps"].append({"id": step["id"], "label": step["label"], "arrows": [_arrow_ids(mech, a) for a in step["arrows"]],
                             "changes": changes, "cations": [{k: v for k, v in c.items() if k != "idx"} for c in cations],
                             "facts": facts})
        snapshots[step["id"]] = (mech.copy(), pos)
    product = mech.product()
    out["product"] = product
    canon = [None] * max(len(options or []), 1 + max(spec["options"], default=-1))
    for i, smi in spec["options"].items():
        if i < 0:
            continue
        c = canonical(smi) if smi else None
        if smi and c is None:
            out["problems"].append(f"option {i + 1}: RDKit cannot read {smi!r}")
        canon[i] = c
    target = canonical(product["smiles"])
    hits = [i for i, c in enumerate(canon) if c and c == target]
    out["option_structures"] = canon
    out["answer_option"] = hits[0] if len(hits) == 1 else None
    if not hits:
        out["problems"].append(f"the mechanism's product {product['smiles']} is none of the options' structures "
                               f"(write 'option <n> <SMILES>' for each structure option)")
    for trap in spec["traps"]:
        if trap["after"] not in snapshots:
            out["problems"].append(f"trap {trap['id']}: 'after {trap['after']}' is not a step id (or start)")
            continue
        base, base_pos = snapshots[trap["after"]]
        branch = base.copy()
        changes = []
        try:
            for arrow in trap["arrows"]:
                changes.append(branch.apply(arrow))
        except ChemProblem as exc:
            out["problems"].append(f"trap {trap['id']}: {exc}")
            continue
        found = branch.check_valence()
        if found:
            out["problems"] += [f"trap {trap['id']}: {p}" for p in found]
            continue
        trap_pos = move_positions(base, branch, changes, base_pos)
        made = canonical(branch.product()["smiles"])
        option = next((i for i, c in enumerate(canon) if c and c == made), None)
        out["trap_options"][trap["id"]] = option
        out["traps"].append({"id": trap["id"], "after": trap["after"], "label": trap["label"],
                             "arrows": [_arrow_ids(branch, a) for a in trap["arrows"]], "changes": changes,
                             "product": branch.product()["smiles"], "option": option,
                             "state": {**branch.state(), "pos": trap_pos}})
    out["step_ids"] = step_ids
    return out


def _arrow_ids(mech: Mech, arrow: dict) -> dict:
    a = lambda n: f"a{n}"  # noqa: E731 - map numbers are the lesson's atom ids
    if arrow["kind"] == "lp":
        return {"kind": "lp", "from": {"atom": a(arrow["src"][0])}, "to": {"atom": a(arrow["dst"][0])}}
    if arrow["kind"] == "bond":
        return {"kind": "bond", "from": {"bond": [a(x) for x in arrow["src"]]}, "to": {"atom": a(arrow["dst"][0])}}
    if arrow["kind"] == "shift":
        return {"kind": "shift", "from": {"bond": [a(arrow["src"][1]), a(arrow["src"][0])]},
                "to": {"atom": a(arrow["dst"][0])}, "group": a(arrow["src"][0])}
    return {"kind": "pi", "from": {"bond": [a(x) for x in arrow["src"]]}, "to": {"bond": [a(x) for x in arrow["dst"]]}}
