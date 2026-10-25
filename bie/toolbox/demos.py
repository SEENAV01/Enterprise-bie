"""Proof clips of the toolbox (Task 046a): one 3–5 second silent clip per demo, made by BIE code only.

Each demo computes its data with the Python adapters (or fetches a model through ``sources``), places it in a
VideoSpec with toolbox blocks, and is rendered by BIE's preview renderer (Chromium + ffmpeg, the remotion-lite path);
the Manim demo renders offline. ``tools/toolbox_demos.py`` runs them, checks every clip and writes contact sheets
and receipts. A demo proves the tools listed in ``tools``; the registry may only say ``demo_proven`` for a tool whose
proof names a demo here.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from bie.brain.assets import AssetLibrary

FPS = 30
FULL = {"x": 0, "y": 0, "w": 1, "h": 1}


@dataclass
class Work:
    folder: Path
    library: AssetLibrary
    opener: object = None
    notes: dict = field(default_factory=dict)

    def src(self, asset) -> str:
        return "assets/" + asset.path


@dataclass(frozen=True)
class Demo:
    id: str
    batch: int
    title: str
    tools: tuple
    capabilities: tuple
    seconds: float
    build: Callable
    kind: str = "web"            # web = BIE blocks through the preview renderer; manim = an offline Manim clip


def scene(layers: list, seconds: float, camera=None) -> dict:
    frames = int(round(seconds * FPS))
    return {"fps": FPS, "width": 1920, "height": 1080, "captions": False,
            "scenes": [{"id": "demo", "duration": frames, "layers": layers, "camera": camera or [{"at": 0, "box": FULL}]}]}


def block(name: str, data: dict, box=None, at: int = 0) -> dict:
    return {"id": name, "type": "block", "block": name, "at": at, "box": box or {"x": 0.02, "y": 0.03, "w": 0.96, "h": 0.94}, "data": data}


# ---------------------------------------------------------------- biology / medical

def cell_sheet(w: Work) -> dict:
    from .adapters import blender
    glb = w.folder / "assets" / "models" / "columnar.glb"
    info = blender.cell_sheet(glb, kind="columnar", rows=5, cols=7)
    w.notes["blender"] = info
    return scene([block("cell_sheet_3d", {"src": "assets/models/columnar.glb", "kind": "columnar", "title": "Columnar epithelium",
                                          "subtitle": f"Blender {info['blender']} model ({info['cells']} cells) · three.js · particles flow through",
                                          "flow": {"particles": 36, "seconds": 2.4}, "focus_cell": "cell_2_3", "focus_at": 1.6,
                                          "camera": {"orbit": 70, "seconds": 4.5}, "badge": "absorption: nutrients cross the sheet"})], 4.5)


def organ_zoom(w: Work) -> dict:
    from . import sources
    tree = sources.servier("2016/10/poumon_01.png", w.library, title="Bronchial tree", opener=w.opener)
    sacs = sources.servier("2016/10/poumon_10.png", w.library, title="Bronchiole and alveoli", opener=w.opener)
    tree_box, sacs_box = {"x": 0.30, "y": 0.06, "w": 0.40, "h": 0.88}, {"x": 0.32, "y": 0.04, "w": 0.36, "h": 0.92}
    layers = [
        {"id": "tree", "type": "image", "at": 0, "until": 66, "box": tree_box, "src": w.src(tree), "credit": "Servier Medical Art · CC BY 4.0"},
        {"id": "title", "type": "title", "at": 0, "until": 24, "box": {"x": 0.03, "y": 0.06, "w": 0.3, "h": 0.2}, "title": "Lung → alveolus",
         "subtitle": "organ zoom"},
        {"id": "sacs", "type": "image", "at": 60, "box": sacs_box, "src": w.src(sacs), "credit": "Servier Medical Art · CC BY 4.0"},
        {"id": "ring", "type": "highlight", "at": 96, "layer": "sacs", "region": {"x": 0.56, "y": 0.66, "w": 0.4, "h": 0.32}, "tone": "warm"},
        {"id": "lab", "type": "label", "at": 104, "box": {"x": 0.43, "y": 0.60, "w": 0.12, "h": 0.06}, "text": "alveolus",
         "anchor": {"layer": "sacs", "point": {"x": 0.72, "y": 0.78}}, "tone": "warm"},
    ]
    camera = [{"at": 0, "box": FULL}, {"at": 20, "layer": "tree", "region": {"x": 0.0, "y": 0.45, "w": 0.45, "h": 0.5}, "frames": 40},
              {"at": 62, "box": FULL, "frames": 1}, {"at": 70, "layer": "sacs", "region": {"x": 0.5, "y": 0.6, "w": 0.5, "h": 0.4}, "frames": 34}]
    return scene(layers, 5.0, camera)


def protein_3dmol(w: Work) -> dict:
    from . import sources
    from .adapters import biology
    asset = sources.rcsb_pdb("1CRN", w.library, opener=w.opener)
    info = biology.pdb_structure((w.library.folder / asset.path).read_text(), pdb_id="1CRN")
    w.notes["biopython"] = {k: info[k] for k in ("atoms", "radius")} | {"chains": [(c["id"], c["residues"]) for c in info["chains"]],
                                                                         "helices": len(info["helices"]), "sheets": len(info["sheets"])}
    chain = info["chains"][0]
    return scene([block("protein_3d", {"src": w.src(asset), "format": "pdb", "title": "Crambin (PDB 1CRN)",
                                       "subtitle": f"{chain['residues']} residues · {len(info['helices'])} helices, {len(info['sheets'])} sheets (Biopython) · 3Dmol.js",
                                       "turn_degrees": 160, "seconds": 4, "badge": "RCSB PDB · CC0"})], 4.0)


def protein_molstar(w: Work) -> dict:
    from . import sources
    asset = sources.rcsb_pdb("1EMA", w.library, opener=w.opener)
    return scene([block("protein_molstar", {"src": w.src(asset), "format": "pdb", "title": "Green fluorescent protein (PDB 1EMA)",
                                            "subtitle": "Mol* cartoon: the beta-barrel", "turn_degrees": 120, "seconds": 4,
                                            "badge": "RCSB PDB · CC0"})], 4.0)


def ecg(w: Work) -> dict:
    from .adapters import biology
    data = biology.ecg(duration=4.0, heart_rate=72, sampling_rate=250)
    w.notes["neurokit2"] = {"r_peaks": data["r_peaks"], "labels": {k: v for k, v in data["labels"].items() if k != "note"}}
    return scene([block("signal_trace", dict(data, title="ECG: one heartbeat after another", subtitle="NeuroKit2 simulation, 72 per minute",
                                              draw_seconds=4.0, label_beats=1, badge="P · QRS · T found by NeuroKit2"))], 4.2)


def nih_heart(w: Work) -> dict:
    from . import sources
    asset = sources.nih3d("3DPX-022787", w.library, opener=w.opener)
    return scene([block("model_3d", {"src": w.src(asset), "title": "Human heart (NIH 3D)", "subtitle": "3DPX-022787 · Public Domain · three.js",
                                     "turn_degrees": 150, "seconds": 4, "credit": asset.credit})], 4.0)


def zanatomy_heart(w: Work) -> dict:
    from . import sources
    asset, info = sources.z_anatomy("CardioVascular41", r"^(left|right) (atrium|ventricle)$|^aortic arch$|^ascending aorta$|pulmonary trunk",
                                    w.library, title="Heart chambers and great vessels", opener=w.opener)
    w.notes["z_anatomy"] = info
    return scene([block("model_3d", {"src": w.src(asset), "title": "Heart chambers (Z-Anatomy)",
                                     "subtitle": f"Blender took {info['objects']} parts from the FBX · left ventricle glows",
                                     "glow": "^left ventricle$", "glow_at": 1.2, "turn_degrees": 120, "seconds": 4, "colour": "#d9686b",
                                     "credit": "Z-Anatomy · CC BY-SA 4.0 (share-alike)"})], 4.0)


def bodyparts_heart(w: Work) -> dict:
    from . import sources
    asset = sources.bodyparts3d("FMA7088", w.library, name="heart", opener=w.opener)
    return scene([block("model_3d", {"src": w.src(asset), "title": "Heart (BodyParts3D, FMA7088)", "subtitle": "OBJ parts joined by trimesh",
                                     "turn_degrees": 140, "seconds": 4, "zoom": 0.7, "zoom_at": 2.2, "credit": "BodyParts3D © DBCLS · CC BY 4.0"})], 4.0)


# ---------------------------------------------------------------- chemistry

def molecule_rdkit(w: Work) -> dict:
    from .adapters import chemistry
    mol = chemistry.molecule("CC(=O)OC1=CC=CC=C1C(=O)O", name="aspirin")
    w.notes["rdkit"] = {"formula": mol["formula"], "atoms": len(mol["atoms"]), "bonds": len(mol["bonds"])}
    return scene([block("molecule_3d", {"text": mol["molblock"], "name": "aspirin", "format": "sdf", "title": f"Aspirin, {mol['formula']}",
                                        "subtitle": "3D shape from RDKit (ETKDG + MMFF) · drawn by 3Dmol.js", "turn_degrees": 220, "seconds": 4})], 4.0)


def molecule_pubchem(w: Work) -> dict:
    from . import sources
    asset = sources.pubchem_sdf("caffeine", w.library, opener=w.opener)
    return scene([block("molecule_3d", {"src": w.src(asset), "format": "sdf", "title": "Caffeine (PubChem 3D record)",
                                        "subtitle": "fetched by name from PubChem · 3Dmol.js", "turn_degrees": 200, "seconds": 3.5})], 3.5)


def reaction(w: Work) -> dict:
    from .adapters import chemistry
    rx = chemistry.reaction("[C:1](=[O:2])[OH:3].[OH:4][C:5]>>[C:1](=[O:2])[O:4][C:5].[OH2:3]", ["CC(=O)O", "OCC"],
                            names={"CC(=O)O": "acetic acid", "CCO": "ethanol", "CCOC(C)=O": "ethyl acetate", "O": "water"})
    if not rx["balanced"]:
        raise RuntimeError("the reaction is not balanced")
    kin = chemistry.kinetics(temperature=1100.0, t_end=0.0006, points=90, species=("H2", "O2", "H2O"))
    w.notes["rdkit_reaction"] = {"balanced": rx["balanced"], "atoms": rx["atoms_left"]}
    w.notes["cantera"] = {"T_start": kin["T"][0], "T_end": kin["T"][-1], "H2O_end": kin["species"]["H2O"][-1]}
    return scene([block("reaction", dict(rx, title="Esterification: acid + alcohol → ester + water", subtitle="RDKit applies the reaction and draws it",
                                         kinetics=dict(kin, caption="below: H2 + O2 → H2O at 1100 K, mole fraction over 0.6 ms (Cantera)")))], 5.0)


# ---------------------------------------------------------------- maths / statistics

def equation(w: Work) -> dict:
    from .adapters import maths
    steps = maths.equation_steps(["3(x - 2) + 4 = 2x + 7", "3x - 6 + 4 = 2x + 7", "3x - 2 = 2x + 7", "x - 2 = 7", "x = 9"])
    if not steps["all_checked"]:
        raise RuntimeError("a step failed SymPy's check")
    return scene([block("equation_steps", {"steps": steps["steps"], "title": "Solve step by step", "subtitle": "every step checked by SymPy",
                                           "step_seconds": 0.85})], 4.5)


def function_graph(w: Work) -> dict:
    from .adapters import maths
    data = maths.function_samples("x^2/4 - 2", x_min=-6, x_max=6)
    return scene([block("function_graph", dict(data, title="A parabola drawn over time", subtitle="points from SymPy + NumPy, drawn by D3",
                                               draw_seconds=3.2, note_latex=r"\frac{dy}{dx} = " + data["derivative_latex"]))], 4.0)


def regression(w: Work) -> dict:
    from .adapters import maths
    xs = [1, 2, 3, 4, 5, 6, 7, 8]
    ys = [2.3, 2.9, 4.2, 4.8, 6.1, 6.4, 7.9, 8.2]
    r = maths.regression(xs, ys)
    w.notes["statsmodels"] = {"slope": r["slope"], "intercept": r["intercept"], "r_squared": r["r_squared"]}
    return scene([block("function_graph", {"x": r["line"]["x"], "y": r["line"]["y"], "points": {"x": xs, "y": ys},
                                           "x_domain": [0, 9], "y_domain": [0, 10], "title": "Best-fit line (least squares)",
                                           "subtitle": "fitted by statsmodels OLS", "draw_start": 1.0, "draw_seconds": 2.0,
                                           "latex": f"y = {r['slope']:.2f}x + {r['intercept']:.2f}", "note": f"R² = {r['r_squared']:.3f}"})], 4.0)


def manim_graph(w: Work) -> dict:
    from .adapters import manim_clips, maths
    data = maths.function_samples("sin(x) + x/4", x_min=-6.28, x_max=6.28, points=160)
    out = w.folder / "demo.mp4"
    info = manim_clips.render("FunctionDraw", {"x": data["x"], "y": data["y"], "title": "y = sin x + x/4",
                                               "note": "SymPy samples · Manim draws (offline path)"}, out)
    w.notes["manim"] = info
    return {"mp4": str(out)}


# ---------------------------------------------------------------- physics

def falling(w: Work) -> dict:
    from .adapters import physics
    data = physics.falling_body(height=20.0, drag=0.12, seconds=3.6)
    w.notes["scipy"] = {"t_ground_drag": data["t_ground_drag"], "t_ground_free": data["t_ground_free"], "terminal_speed": data["terminal_speed"]}
    return scene([block("falling_body", dict(data, title="Falling from 20 m", subtitle="with and without air drag (SciPy ODE, NumPy)",
                                             badge=f"lands at {data['t_ground_free']:.2f} s without air, {data['t_ground_drag']:.2f} s with drag"))], 4.0)


def wave(w: Work) -> dict:
    from .adapters import physics
    data = physics.wave(seconds=4.0)
    return scene([block("wave", dict(data, title="Two waves meet: a standing wave", subtitle="computed with NumPy"))], 4.0)


def matter(w: Work) -> dict:
    bodies = [{"shape": "box", "x": 0.25 + 0.06 * (i % 4), "y": 0.1 - 0.12 * (i // 4), "size": 0.08, "angle": 0.2 * i} for i in range(8)]
    bodies += [{"shape": "circle", "x": 0.75, "y": 0.05, "size": 0.09, "bounce": 0.7, "colour": "#ff6b6b"}]
    return scene([block("rigid_bodies_2d", {"bodies": bodies, "ramp": {"x": 0.72, "y": 0.55, "w": 0.35, "angle": 0.35}, "seconds": 4,
                                            "title": "Boxes fall and stack, a ball rolls", "subtitle": "Matter.js, fixed time step",
                                            "badge": "physics_sim_2d"})], 4.0)


def collision(w: Work) -> dict:
    # Momentum passes along: the moving ball stops, the ball it hits rolls on and knocks the tower over.
    bodies = [{"shape": "sphere", "size": 1.0, "position": [-4.5, 0.5, 0], "velocity": [7, 0, 0], "mass": 1},
              {"shape": "sphere", "size": 1.0, "position": [-0.5, 0.5, 0], "mass": 1}]
    bodies += [{"shape": "box", "size": 0.8, "position": [3.2, 0.4 + 0.8 * i, 0], "mass": 0.3, "colour": "#9fb3bf"} for i in range(4)]
    return scene([block("collision_3d", {"bodies": bodies, "seconds": 4, "restitution": 0.9, "title": "A collision passes momentum on",
                                         "subtitle": "cannon-es computes, three.js draws", "badge": "physics_sim_3d",
                                         "start_degrees": 8, "turn_degrees": 22, "distance": 11, "camera_height": 4.5})], 4.0)


# ---------------------------------------------------------------- computer science

def graph_bfs(w: Work) -> dict:
    from .adapters import graphs
    data = graphs.layout_and_bfs([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("C", "E"), ("E", "F"), ("D", "G"), ("F", "G"), ("B", "H")], "A")
    w.notes["networkx"] = {"order": data["order"]}
    return scene([block("network_graph", dict(data, title="Breadth-first search from A", subtitle="layout and order from NetworkX",
                                              step_seconds=0.42))], 4.5)


# Every 3D block draws through @remotion/three, React Three Fiber and drei on three.js.
THREE_STACK = ("three", "react-three-fiber", "drei", "remotion-three")

DEMOS = (
    Demo("bio-cell-sheet-flow", 1, "Blender-made columnar epithelium in three.js with particles flowing through",
         ("blender", *THREE_STACK), ("cell_sheet_3d", "particle_flow", "focus_glow"), 4.5, cell_sheet),
    Demo("bio-organ-zoom", 1, "Lung to alveolus zoom on Servier pictures", ("servier-medical-art", "bie-blocks"),
         ("organ_zoom", "focus_glow"), 5.0, organ_zoom),
    Demo("bio-protein-3dmol", 1, "Crambin from the PDB, read by Biopython, drawn by 3Dmol.js", ("rcsb-pdb", "biopython", "3dmol"),
         ("protein_3d",), 4.0, protein_3dmol),
    Demo("bio-protein-molstar", 1, "Green fluorescent protein in Mol*", ("molstar", "rcsb-pdb"), ("protein_3d",), 4.0, protein_molstar),
    Demo("bio-ecg", 1, "An ECG simulated by NeuroKit2 drawn on its paper", ("neurokit2", "d3"), ("ecg_trace", "signal_plot"), 4.2, ecg),
    Demo("bio-heart-nih3d", 1, "NIH 3D heart model turning", ("nih-3d", *THREE_STACK), ("anatomy_3d",), 4.0, nih_heart),
    Demo("bio-heart-zanatomy", 1, "Z-Anatomy heart chambers exported by Blender, left ventricle glowing",
         ("z-anatomy", "blender", *THREE_STACK),
         ("anatomy_3d", "focus_glow"), 4.0, zanatomy_heart),
    Demo("bio-heart-bodyparts3d", 1, "BodyParts3D heart joined by trimesh, zooming in",
         ("bodyparts3d", "trimesh", *THREE_STACK),
         ("anatomy_3d", "organ_zoom"), 4.0, bodyparts_heart),
    Demo("chem-molecule-rdkit", 1, "Aspirin in 3D from RDKit, drawn by 3Dmol.js", ("rdkit", "3dmol"), ("molecule_3d",), 4.0, molecule_rdkit),
    Demo("chem-molecule-pubchem", 1, "Caffeine's 3D record from PubChem", ("pubchem", "3dmol"), ("molecule_3d",), 3.5, molecule_pubchem),
    Demo("chem-reaction", 1, "Esterification by RDKit and H2 + O2 kinetics by Cantera", ("rdkit", "cantera", "d3", "bie-blocks"),
         ("reaction_steps", "chart_bar_line_pie"), 5.0, reaction),
    Demo("maths-equation", 1, "A linear equation solved step by step, every step checked by SymPy, typeset by KaTeX",
         ("sympy", "katex"), ("equation_transform",), 4.5, equation),
    Demo("maths-function-graph", 1, "A parabola drawn over time", ("sympy", "numpy", "d3"), ("function_graph",), 4.0, function_graph),
    Demo("maths-regression", 1, "A least-squares line fitted by statsmodels", ("statsmodels", "d3"), ("function_graph", "chart_bar_line_pie"),
         4.0, regression),
    Demo("maths-manim", 1, "A function drawn by Manim (offline path)", ("manim", "sympy"), ("function_graph",), 4.1, manim_graph, kind="manim"),
    Demo("physics-falling", 1, "A falling body with and without air drag", ("scipy", "numpy", "d3"), ("physics_sim_2d", "function_graph"),
         4.0, falling),
    Demo("physics-wave", 1, "Two travelling waves make a standing wave", ("numpy", "d3"), ("wave_motion",), 4.0, wave),
    Demo("physics-matter", 1, "Boxes and a ball under gravity", ("matter-js",), ("physics_sim_2d",), 4.0, matter),
    Demo("physics-collision-3d", 1, "A ball passes its momentum on and knocks a tower over (3D)", ("cannon-es", *THREE_STACK), ("physics_sim_3d",), 4.0, collision),
    Demo("cs-graph-bfs", 1, "Breadth-first search on a graph", ("networkx", "d3"), ("network_graph",), 4.5, graph_bfs),
)


def by_id(demo_id: str) -> Demo:
    for d in DEMOS:
        if d.id == demo_id:
            return d
    raise KeyError(demo_id)
