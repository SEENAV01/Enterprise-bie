"""Biology computed in Python (NeuroKit2, Biopython) for BIE's web blocks (Task 046a).

- ``ecg``: a realistic simulated ECG (NeuroKit2's ECGSYN model) with its R peaks and the P, Q, S, T points.
- ``pdb_structure``: what a PDB file holds (chains, residues, the alpha-carbon trace, helices and sheets) read with
  Biopython, for labels and camera framing; the PDB text itself goes to 3Dmol.js or Mol* to be drawn.
"""
from __future__ import annotations

import io
import warnings

from .base import clean, need


def ecg(*, duration: float = 4.0, heart_rate: int = 72, sampling_rate: int = 250, seed: int = 7) -> dict:
    nk = need("neurokit2")
    np = need("numpy")
    signal = nk.ecg_simulate(duration=duration, sampling_rate=sampling_rate, heart_rate=heart_rate, random_state=seed,
                             method="ecgsyn")
    cleaned = nk.ecg_clean(signal, sampling_rate=sampling_rate)
    _, info = nk.ecg_peaks(cleaned, sampling_rate=sampling_rate)
    r_peaks = [int(i) for i in info["ECG_R_Peaks"]]
    labels = {"R": r_peaks}
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            _, waves = nk.ecg_delineate(cleaned, r_peaks, sampling_rate=sampling_rate, method="peak")
        for key, name in (("ECG_P_Peaks", "P"), ("ECG_Q_Peaks", "Q"), ("ECG_S_Peaks", "S"), ("ECG_T_Peaks", "T")):
            labels[name] = [int(i) for i in waves.get(key, []) if i == i]          # drop NaN
    except Exception as exc:                           # the delineation is a label aid, never a reason to fail
        labels["note"] = f"delineation skipped: {type(exc).__name__}"
    mv = np.asarray(signal, dtype=float)
    return clean({"sampling_rate": sampling_rate, "duration": duration, "heart_rate": heart_rate, "mv": mv, "r_peaks": r_peaks,
                  "labels": labels, "mv_min": float(mv.min()), "mv_max": float(mv.max()),
                  "computed_by": f"neurokit2 {nk.__version__} ecg_simulate(ecgsyn), ecg_peaks, ecg_delineate"}, 4)


def _secondary(pdb_text: str) -> dict:
    """HELIX and SHEET records by their fixed PDB columns; a malformed record is skipped, never fatal."""
    helices, sheets = [], []
    for line in pdb_text.splitlines():
        try:
            if line.startswith("HELIX "):
                helices.append({"chain": line[19].strip(), "start": int(line[21:25]), "end": int(line[33:37])})
            elif line.startswith("SHEET "):
                sheets.append({"chain": line[21].strip(), "start": int(line[22:26]), "end": int(line[33:37])})
        except (ValueError, IndexError):
            continue
    return {"helices": helices, "sheets": sheets}


def pdb_structure(pdb_text: str, *, pdb_id: str = "") -> dict:
    need("biopython")
    from Bio.PDB import PDBParser
    from Bio.PDB.PDBExceptions import PDBConstructionWarning
    np = need("numpy")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", PDBConstructionWarning)
        structure = PDBParser(QUIET=True).get_structure(pdb_id or "structure", io.StringIO(pdb_text))
    model = next(iter(structure))
    chains, all_ca = [], []
    for chain in model:
        ca = [atom.coord.tolist() for residue in chain for atom in residue if atom.get_id() == "CA"]
        residues = [r for r in chain if r.id[0] == " "]
        if residues:
            chains.append({"id": chain.id, "residues": len(residues), "ca": ca,
                           "sequence_start": residues[0].get_resname(), "sequence_end": residues[-1].get_resname()})
            all_ca.extend(ca)
    coords = np.asarray(all_ca or [[0.0, 0.0, 0.0]], dtype=float)
    centre = coords.mean(axis=0)
    radius = float(np.sqrt(((coords - centre) ** 2).sum(axis=1)).max())
    header = structure.header or {}
    return clean({"id": pdb_id, "name": header.get("name", ""), "atoms": sum(1 for _ in model.get_atoms()), "chains": chains,
                  "centre": centre, "radius": radius, **_secondary(pdb_text), "computed_by": "Bio.PDB.PDBParser"}, 3)
