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
    # A stack of boxes is chaotic (a 1e-9 shift can leave it standing), so these numbers were swept in cannon-es with the
    # start positions jittered from 1e-9 to 2e-3: the tower fell in 8 of 8 runs.
    bodies = [{"shape": "sphere", "size": 1.6, "position": [-4.5, 0.8, 0], "velocity": [10, 0, 0], "mass": 3},
              {"shape": "sphere", "size": 1.6, "position": [-1.0, 0.8, 0], "mass": 3}]
    bodies += [{"shape": "box", "size": 0.6, "position": [2.2, 0.3 + 0.6 * i, 0], "mass": 0.1, "colour": "#9fb3bf"} for i in range(5)]
    return scene([block("collision_3d", {"bodies": bodies, "seconds": 4, "restitution": 0.95, "friction": 0.05,
                                         "title": "A collision passes momentum on",
                                         "subtitle": "cannon-es computes, three.js draws", "badge": "physics_sim_3d",
                                         "start_degrees": 8, "turn_degrees": 22, "distance": 11, "camera_height": 4.5})], 4.0)


# ---------------------------------------------------------------- computer science

def graph_bfs(w: Work) -> dict:
    from .adapters import graphs
    data = graphs.layout_and_bfs([("A", "B"), ("A", "C"), ("B", "D"), ("C", "D"), ("C", "E"), ("E", "F"), ("D", "G"), ("F", "G"), ("B", "H")], "A")
    w.notes["networkx"] = {"order": data["order"]}
    return scene([block("network_graph", dict(data, title="Breadth-first search from A", subtitle="layout and order from NetworkX",
                                              step_seconds=0.42))], 4.5)


# ================================================================ batch 2: electrical, mechanical, earth, space, aerospace

def _own_glb(w: Work, data: bytes, title: str, made_by: str):
    """A model BIE's own code made (CadQuery, AeroSandbox), kept in the asset library like any other model."""
    return w.library.add_bytes(data, mime="model/gltf-binary", source="bie_toolbox", title=title, page_url="",
                               licence="BIE's own model (made by BIE code)", licence_url="", author="BIE", credit=f"made by BIE with {made_by}",
                               tags=["bie-made", "3d"])


def rc_circuit(w: Work) -> dict:
    from .adapters import electrical
    parts = electrical.circuit_parts([("SourceV", "up", "5 V", {}), ("Switch", "right", "switch", {}), ("Resistor", "right", "1 kΩ", {}),
                                      ("Capacitor", "down", "100 µF", {}), ("Line", "tox:0", "", {})])
    trace = electrical.rc_charge(1000.0, 100e-6, 5.0)
    if not trace["agree"]:
        raise RuntimeError("ngspice and lcapy disagree")
    w.notes["ngspice_lcapy"] = {"tau_s": trace["tau"], "max_difference_V": trace["max_difference"]}
    return scene([block("circuit_build", dict(parts, trace=trace, title="An RC circuit, part by part", piece_seconds=0.32, trace_seconds=1.6,
                                              latex=r"V_C(t) = 5\left(1 - e^{-t/RC}\right),\; RC = 0.1\,\mathrm{s}",
                                              subtitle="drawn by schemdraw · simulated by ngspice · exact formula from lcapy",
                                              badge="ngspice matches lcapy"))], 4.6)


def step_response(w: Work) -> dict:
    from .adapters import electrical
    data = electrical.step_responses((0.2, 0.5, 1.0), wn=2.0, t_end=8.0)
    if not data["all_checked"]:
        raise RuntimeError("python-control and scipy.signal disagree")
    w.notes["python_control"] = [{"zeta": r["zeta"], "overshoot_percent": r["overshoot_percent"]} for r in data["responses"]]
    series = [{"x": data["t"], "y": r["y"], "label": f"ζ = {r['zeta']}", "start": 0.3 + 0.5 * k, "seconds": 2.0}
              for k, r in enumerate(data["responses"])]
    return scene([block("xy_lines", {"series": series, "title": "Step response: damping decides the overshoot",
                                     "subtitle": "python-control computes · scipy.signal checks", "x_label": "time (s)", "y_label": "output",
                                     "legend_box": True,
                                     "latex": r"G(s) = \frac{\omega_n^2}{s^2 + 2\zeta\omega_n s + \omega_n^2}",
                                     "note": f"ζ = 0.2 overshoots {data['responses'][0]['overshoot_percent']:.0f}%"})], 4.2)


def beam(w: Work) -> dict:
    from .adapters import mechanics
    data = mechanics.beam_point_load(6.0, 20e3, 2.0)
    if not data["agree"]:
        raise RuntimeError("PyNite and sympy.physics disagree")
    w.notes["pynite"] = {"max_deflection_mm": data["max_deflection_mm"], "sympy_mm": data["sympy_max_deflection_mm"], "max_moment_kNm": data["max_moment_kNm"]}
    return scene([block("beam_load", dict(data, title="A 6 m steel beam under a 20 kN load", subtitle="PyNite (finite elements) · checked by sympy.physics",
                                          badge="PyNite = sympy.physics"))], 4.0)


def flange(w: Work) -> dict:
    from .adapters import mechanics
    glb, facts = mechanics.flange_glb()
    w.notes["cadquery"] = facts
    asset = _own_glb(w, glb, "Pipe flange (CadQuery)", "CadQuery")
    return scene([block("model_3d", {"src": w.src(asset), "title": "A pipe flange from CadQuery", "colour": "#b8c4cc", "turn_degrees": 200, "seconds": 4,
                                     "subtitle": f"OpenCascade solid · {facts['volume_cm3']:.0f} cm³ · {facts['mass_kg']:.2f} kg of steel",
                                     "start_degrees": 20, "spin": True, "camera_height": 2.2, "distance": 3.8})], 4.0)


def rankine_cycle(w: Work) -> dict:
    from .adapters import mechanics
    r = mechanics.rankine(80.0, 0.1, 480.0)
    w.notes["coolprop"] = {"efficiency": r["efficiency"]}
    st = r["states"]
    dome = r["dome"]                                    # one line over the top: liquid side up, vapour side down
    series = [{"x": dome["s_liquid"] + dome["s_vapour"][::-1], "y": dome["T_C"] + dome["T_C"][::-1], "colour": "#6fb7ff", "start": 0.1,
               "seconds": 0.9, "width": 4, "label": "saturation dome"},
              {"x": [st[0]["s"], st[1]["s"]], "y": [st[0]["T_C"], st[1]["T_C"]], "colour": "#c79bff", "start": 1.0, "seconds": 0.3, "label": "pump"},
              {"x": r["heating"]["s"], "y": r["heating"]["T_C"], "colour": "#ff6b6b", "start": 1.3, "seconds": 1.0, "label": "boiler"},
              {"x": [st[2]["s"], st[3]["s"]], "y": [st[2]["T_C"], st[3]["T_C"]], "colour": "#38d3c3", "start": 2.3, "seconds": 0.5, "label": "turbine"},
              {"x": [st[3]["s"], st[0]["s"]], "y": [st[3]["T_C"], st[0]["T_C"]], "colour": "#ffb35c", "start": 2.8, "seconds": 0.6, "label": "condenser"}]
    points = [{"x": p["s"], "y": p["T_C"], "label": p["name"], "at": 1.0 + 0.6 * k} for k, p in enumerate(st)]
    return scene([block("xy_lines", {"series": series, "points": points, "title": "A steam power plant on a T–s chart",
                                     "subtitle": "Rankine cycle, 80 bar and 480 °C · water properties from CoolProp",
                                     "x_label": "entropy s (kJ/kg·K)", "y_label": "temperature (°C)", "legend_box": True,
                                     "note": f"efficiency {100 * r['efficiency']:.1f}%"})], 4.2)


def heat_plate(w: Work) -> dict:
    from .adapters import mechanics
    data = mechanics.heated_plate()
    w.notes["scikit_fem"] = {"elements": data["elements"]}
    return scene([block("heat_plate", dict(data, title="Heat spreading through a plate", subtitle="finite elements by scikit-fem · arrows = heat flow",
                                           badge=f"{data['elements']} triangles"))], 4.0)


def relief(w: Work) -> dict:
    import math
    from PIL import Image
    from .adapters import earth
    region = (70.0, 100.0, 20.0, 40.0)
    out = w.folder / "relief.png"
    data = earth.relief(region, out, profile=((77.0, 22.0), (90.0, 36.0)))
    asset = w.library.add_bytes(out.read_bytes(), mime="image/png", source="pygmt", title="Himalaya and Tibet, shaded relief",
                                page_url=earth.EARTH_RELIEF["source"], licence=earth.EARTH_RELIEF["licence"], licence_url="",
                                author="BIE with PyGMT; data SRTM15+ (Tozer et al., 2019)", credit="Relief: SRTM15+ V2.7 via GMT · map by BIE (PyGMT)",
                                tags=["relief", "map"])
    width_px, height_px = Image.open(out).size
    box_w = 0.52
    box = {"x": 0.02, "y": 0.15, "w": box_w, "h": box_w * 1920 / (width_px / height_px) / 1080}
    merc = lambda lat: math.log(math.tan(math.pi / 4 + math.radians(lat) / 2))
    pts = [{"x": (lon - region[0]) / (region[1] - region[0]), "y": (merc(region[3]) - merc(lat)) / (merc(region[3]) - merc(region[2]))}
           for lon, lat in zip(data["profile"]["lon"][::8], data["profile"]["lat"][::8])]
    w.notes["pygmt"] = {"min_m": data["min_m"], "max_m": data["max_m"], "profile_points": len(data["profile"]["km"])}
    layers = [
        {"id": "title", "type": "title", "at": 0, "box": {"x": 0.02, "y": 0.0, "w": 0.7, "h": 0.14}, "title": "Crossing the Himalaya",
         "subtitle": "shaded relief by PyGMT (GMT 6, SRTM15+) · the height along the line"},
        {"id": "relief", "type": "image", "at": 0, "box": box, "src": w.src(asset), "credit": "SRTM15+ V2.7 · PyGMT"},
        {"id": "line", "type": "flow", "at": 12, "layer": "relief", "path": pts, "particles": 10, "seconds": 2, "tone": "warm"},
        block("xy_lines", {"series": [{"x": data["profile"]["km"], "y": data["profile"]["elevation_m"], "colour": "#ffb35c", "fill": True,
                                       "start": 0.6, "seconds": 2.6}], "x_label": "km along the line", "y_label": "height (m)",
                           "note": f"highest {max(data['profile']['elevation_m']):.0f} m"},
              box={"x": 0.55, "y": 0.15, "w": 0.44, "h": 0.8}),
    ]
    return scene(layers, 4.2)


def seismic_rays(w: Work) -> dict:
    from .adapters import earth
    data = earth.ray_paths(70.0, 15.0)
    w.notes["obspy"] = {r["phase"]: r["time_s"] for r in data["rays"]}
    return scene([block("earth_section", dict(data, title="Seismic waves through the Earth", subtitle="ray paths and times from ObsPy TauP (IASP91 model)",
                                              travel_seconds=3.2, badge="P is fast, S is slower and cannot cross the liquid core"))], 4.2)


def quake_map(w: Work) -> dict:
    from . import sources
    asset, rows = sources.usgs_quakes("2025-01-01", "2025-12-31", w.library, magnitude=6.0, opener=w.opener)
    w.notes["usgs"] = {"earthquakes": len(rows), "largest": max(r["magnitude"] for r in rows)}
    return scene([block("world_points", {"points": rows, "title": "A year of strong earthquakes (2025)", "seconds": 3.4,
                                         "subtitle": "magnitude 6 and above · USGS catalogue · Natural Earth map (d3-geo)",
                                         "credit": "Earthquakes: U.S. Geological Survey (public domain) · Map: Natural Earth (public domain)"})], 4.2)


def plates(w: Work) -> dict:
    from . import sources
    from .adapters import earth
    model = sources.gplates_model("muller2019", opener=w.opener)
    data = earth.reconstruct(model["rotations"], model["coastlines"], ages=tuple(range(200, -1, -10)), min_step_deg=1.5, min_points=8)
    w.notes["pygplates"] = {"frames": len(data["frames"]), "points_per_frame": data["frames"][0]["points"]}
    return scene([block("plate_frames", dict(data, title="The continents drifting apart", subtitle="coastlines moved by pyGPlates, 200 million years to today",
                                             seconds=3.6, credit=model["credit"]))], 4.2)


def planet_orbits(w: Work) -> dict:
    from .adapters import astro
    data = astro.orbits("2026-01-01", 687, 3)
    w.notes["skyfield_astropy"] = {p["name"]: p["kepler_period_days"] for p in data["planets"]}
    return scene([block("orbits", dict(data, title="The inner planets in 2026–27", subtitle="positions from NASA JPL DE421 by Skyfield · periods by Astropy (Kepler)",
                                       seconds=3.8, badge="Mars needs 687 days for one orbit"))], 4.2)


def night_sky(w: Work) -> dict:
    from .adapters import astro
    data = astro.sky(28.61, 77.21, "2026-01-15T20:00:00")
    w.notes["skyfield"] = {"stars": data["count"], "planets": [p["name"] for p in data["planets"]]}
    return scene([block("sky_dome", dict(data, title="The sky over New Delhi", subtitle="15 January 2026, 8 pm · Hipparcos stars brighter than magnitude 3.5",
                                         place_name="New Delhi", time_label="15 Jan 2026, 8:00 pm IST",
                                         names={"32349": "Sirius", "27989": "Betelgeuse", "24436": "Rigel", "37279": "Procyon",
                                                "21421": "Aldebaran", "24608": "Capella"},
                                         credit="Stars: Hipparcos Catalogue (ESA 1997) via CDS · positions by Skyfield"))], 4.0)


def earthrise(w: Work) -> dict:
    from . import sources
    asset = sources.nasa_image("as08-14-2383", w.library, size="medium", opener=w.opener)
    layers = [
        {"id": "photo", "type": "image", "at": 0, "box": {"x": 0.21875, "y": 0.0, "w": 0.5625, "h": 1.0}, "src": w.src(asset), "credit": asset.credit},
        {"id": "ring", "type": "highlight", "at": 70, "layer": "photo", "region": {"x": 0.47, "y": 0.44, "w": 0.19, "h": 0.15}, "tone": "accent"},
        {"id": "lab", "type": "label", "at": 80, "box": {"x": 0.6, "y": 0.36, "w": 0.1, "h": 0.05}, "text": "Earth",
         "anchor": {"layer": "photo", "point": {"x": 0.6, "y": 0.47}}, "tone": "accent"},
        {"id": "title", "type": "title", "at": 0, "until": 40, "box": {"x": 0.02, "y": 0.04, "w": 0.3, "h": 0.2}, "title": "Earthrise",
         "subtitle": "Apollo 8, 1968 (NASA)"},
    ]
    # a wide zoom that keeps the Moon's horizon in view: the point of Earthrise is the Earth seen from the Moon
    camera = [{"at": 0, "box": FULL}, {"at": 30, "layer": "photo", "region": {"x": 0.2, "y": 0.3, "w": 0.66, "h": 0.6}, "frames": 50}]
    return scene(layers, 4.2, camera)


def aircraft(w: Work) -> dict:
    from .adapters import aero
    glb, facts = aero.trainer_aircraft()
    w.notes["aerosandbox"] = {"cl_per_degree": facts["cl_per_degree"], "wing_area_m2": facts["wing_area_m2"]}
    asset = _own_glb(w, glb, "Trainer aircraft (AeroSandbox)", "AeroSandbox")
    curve = facts["lift_curve"]
    return scene([
        block("model_3d", {"src": w.src(asset), "title": "A trainer aircraft from AeroSandbox", "colour": "#d8e2e8", "turn_degrees": 160, "seconds": 4,
                           "subtitle": f"NACA 2412 wing, span {facts['span_m']:.1f} m", "start_degrees": 210, "spin": True,
                           "camera_height": 1.2, "distance": 3.6},
              box={"x": 0.0, "y": 0.0, "w": 0.6, "h": 1.0}),
        block("xy_lines", {"series": [{"x": [c["alpha_deg"] for c in curve], "y": [c["CL"] for c in curve], "label": "lift", "start": 0.8, "seconds": 2.4}],
                           "points": [{"x": c["alpha_deg"], "y": c["CL"], "at": 0.8 + 0.5 * k} for k, c in enumerate(curve)],
                           "x_label": "angle of attack (°)", "y_label": "lift coefficient CL",
                           "note": f"+{facts['cl_per_degree']:.3f} CL per degree (vortex lattice)"},
              box={"x": 0.58, "y": 0.12, "w": 0.41, "h": 0.82}),
    ], 4.2)


def climb(w: Work) -> dict:
    from .adapters import aero
    data = aero.climb()
    w.notes["jsbsim"] = {"best_climb_fpm": data["best_climb_fpm"], "end_altitude_ft": data["altitude_ft"][-1]}
    return scene([block("flight_profile", dict(data, title="A Cessna 172 climbs to 2,500 ft", subtitle="flight dynamics by JSBSim (c172x and its autopilot)",
                                               seconds=3.8, badge="120 simulated seconds in 4"))], 4.2)

# ---------------------------------------------------------------- batch 3: geography, history, polity

BNSS = "AC_CEN_5_23_00049_202346_1719552320687"        # India Code's id of the Bharatiya Nagarik Suraksha Sanhita, 2023
NE_CREDIT = "Map: Natural Earth (public domain), India's own boundary view · BIE (Shapely, d3-geo)"


def india_state(w: Work) -> dict:
    from .adapters import maps
    data = maps.india(["Uttar Pradesh"])
    # Natural Earth's own state/UT labels are older than some changes (2019's Jammu and Kashmir), so only the count is shown
    w.notes["shapely"] = {"states_and_uts": len(data["states"]), "uttar_pradesh_km2": next(s["area_km2"] for s in data["states"] if s["highlight"])}
    return scene([block("india_map", dict(data, title="Uttar Pradesh on the map of India",
                                          subtitle=f"{len(data['states'])} states and union territories · the area is computed by BIE",
                                          highlight_at=0.5, zoom_at=1.4, zoom_seconds=1.5, credit=NE_CREDIT))], 4.2)


def gt_road(w: Work) -> dict:
    from .adapters import maps
    data = maps.india([], tolerance=0.03)
    route = maps.route(["Kolkata", "Dhanbad", "Varanasi", "Prayagraj", "Kanpur", "Agra", "Delhi", "Panipat", "Ambala", "Ludhiana",
                        "Amritsar", "Lahore", "Rawalpindi", "Peshawar", "Kabul"])
    w.notes["route"] = {"stops": len(route["stops"]), "total_km": route["total_km"]}
    return scene([block("india_map", dict(data, route=route, title="The Grand Trunk Road, Kolkata to Kabul",
                                          subtitle="towns from Natural Earth · straight great-circle legs, not road distances",
                                          route_at=0.5, route_seconds=3.2, credit=NE_CREDIT))], 4.2)


def national_movement(w: Work) -> dict:
    events = [{"date": "1857-05-10", "label": "Revolt of 1857 begins at Meerut"},
              {"date": "1885-12-28", "label": "Indian National Congress founded"},
              {"date": "1905-10-16", "label": "Partition of Bengal"},
              {"date": "1919-04-13", "label": "Jallianwala Bagh massacre"},
              {"date": "1920-08-01", "label": "Non-cooperation movement"},
              {"date": "1930-03-12", "label": "Dandi March begins"},
              {"date": "1942-08-08", "label": "Quit India resolution"},
              {"date": "1947-08-15", "label": "Independence"},
              {"date": "1950-01-26", "label": "Constitution in force"}]
    return scene([block("timeline_build", {"events": events, "start": "1850-01-01", "end": "1955-01-01", "tick_years": 10, "seconds": 3.3,
                                           "title": "Towards independence, 1857 to 1950", "subtitle": "a D3 time scale; each event on its own date",
                                           "eras": [{"from": "1857-01-01", "to": "1885-12-28", "label": "after the Revolt"},
                                                    {"from": "1885-12-28", "to": "1919-04-13", "label": "early nationalism"},
                                                    {"from": "1919-04-13", "to": "1947-08-15", "label": "mass movements"}]})], 4.2)


BILL_TO_ACT = """flowchart LR
  A["Bill introduced<br/>in one House"] --> B["First reading"]
  B --> C["Committee<br/>(if referred)"]
  C --> D["Second reading:<br/>clause by clause"]
  D --> E["Third reading:<br/>passed"]
  E --> F["Other House:<br/>same stages"]
  F --> G{"Both Houses<br/>agree?"}
  G -- "yes" --> I["President's assent<br/>(Article 111)"]
  G -- "no" --> H["Joint sitting<br/>(Article 108)"]
  H --> I
  I --> J(["Act of Parliament"])
"""


def bill_to_act(w: Work) -> dict:
    order = ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"]
    edges = [("A", "B"), ("B", "C"), ("C", "D"), ("D", "E"), ("E", "F"), ("F", "G"), ("G", "I"), ("G", "H"), ("H", "I"), ("I", "J")]
    return scene([block("mermaid_build", {"source": BILL_TO_ACT, "order": order, "edges": edges, "seconds": 3.3,
                                          "title": "How a Bill becomes an Act (Parliament of India)",
                                          "subtitle": "written in Mermaid · laid out by elkjs · Articles 107 to 111 of the Constitution",
                                          "badge": "Mermaid + ELK layout"})], 4.2)


def _picture_name(asset) -> str:
    """The caption is the archive's own title and author: BIE does not describe a picture it has not looked at."""
    title = asset.title.removeprefix("File:").rsplit(".", 1)[0].replace("_", " ")
    return f"{title} · {asset.author}"[:70] if asset.author else title[:70]


def archive_images(w: Work) -> dict:
    from . import sources
    old = sources.commons_image("File:Gandhiji Leading Salt satyagrah.jpg", w.library, tags=["history", "salt march"], width=960, opener=w.opener)
    new = sources.openverse_image("bafa11dc-b447-4e43-804c-c3f8f3eca309", w.library, tags=["history", "salt march"], opener=w.opener)
    w.notes["licences"] = {"commons": old.licence, "openverse": new.licence}
    left, right = {"x": 0.03, "y": 0.16, "w": 0.45, "h": 0.66}, {"x": 0.52, "y": 0.16, "w": 0.45, "h": 0.66}
    layers = [
        {"id": "title", "type": "title", "at": 0, "box": {"x": 0.03, "y": 0.02, "w": 0.9, "h": 0.12}, "title": "The Salt March in two open archives",
         "subtitle": "Wikimedia Commons (left) and Openverse (right), each picture with its licence"},
        {"id": "old", "type": "image", "at": 6, "box": left, "src": w.src(old), "credit": f"Wikimedia Commons · {old.licence}"},
        {"id": "new", "type": "image", "at": 40, "box": right, "src": w.src(new), "credit": f"Openverse · {new.licence}"},
        {"id": "c1", "type": "label", "at": 20, "box": {"x": 0.06, "y": 0.85, "w": 0.39, "h": 0.06}, "text": _picture_name(old), "tone": "accent"},
        {"id": "c2", "type": "label", "at": 54, "box": {"x": 0.55, "y": 0.85, "w": 0.39, "h": 0.06}, "text": _picture_name(new), "tone": "warm"},
    ]
    camera = [{"at": 0, "box": FULL}, {"at": 70, "box": {"x": 0.02, "y": 0.08, "w": 0.96, "h": 0.9}, "frames": 56}]
    return scene(layers, 4.2, camera)


# ---------------------------------------------------------------- batch 3: economics, commerce, management

def gdp_growth(w: Work) -> dict:
    from . import sources
    asset, rows, meta = sources.world_bank("NY.GDP.MKTP.KD.ZG", ["IND"], 1991, 2024, w.library, opener=w.opener)
    years, values = [r["year"] for r in rows], [r["value"] for r in rows]
    low = min(range(len(values)), key=lambda i: values[i])
    w.notes["world_bank"] = {"years": f"{years[0]}-{years[-1]}", "lowest": [years[low], round(values[low], 1)]}
    return scene([block("chartjs_build", {"labels": [str(y) for y in years], "values": values, "highlight": low, "unit": " %",
                                          "y_label": "GDP growth, % a year", "seconds": 3.2,
                                          "note": f"{years[low]}: {values[low]:+.1f} %, the lowest since {years[0]}",
                                          "title": "India's economy, growth year by year", "subtitle": f"World Bank: {meta['name']} · Chart.js",
                                          "credit": asset.credit})], 4.2)


def wealth_health(w: Work) -> dict:
    from . import sources
    from .adapters import economics
    countries = ["IND", "CHN", "USA", "BRA", "NGA", "ETH", "IDN", "JPN"]
    series, credits = {}, []
    for key, code in (("x", "NY.GDP.PCAP.PP.KD"), ("y", "SP.DYN.LE00.IN"), ("size", "SP.POP.TOTL")):
        asset, rows, _ = sources.world_bank(code, countries, 1995, 2022, w.library, opener=w.opener)
        series[key] = rows
        credits.append(code)
    data = economics.joined_frames(series, list(range(1995, 2023)))
    w.notes["world_bank"] = {"countries": len(data["countries"]), "frames": len(data["frames"])}
    return scene([block("vega_build", dict(data, key="wealth-health", trail=["IND", "CHN"], seconds=3.4,
                                           x_title="income per person (GDP per capita, PPP, constant 2021 $; log scale)",
                                           y_title="life expectancy at birth (years)", x_domain=[500, 90000], y_domain=[44, 86],
                                           size_domain=[0, 1450000000], title="Wealth and health, 1995 to 2022",
                                           subtitle="World Bank data · compiled by Vega-Lite, drawn by Vega · India and China leave a trail",
                                           credit="World Bank, World Development Indicators (" + ", ".join(credits) + "), CC BY 4.0"))], 4.2)


def cobb_douglas(w: Work) -> dict:
    from .adapters import economics
    cd = economics.cobb_douglas(alpha=0.4, beta=0.6, r=2.0, w=1.0)
    w.notes["numpy"] = {"k_over_l": cd["k_over_l"], "returns_to_scale": cd["returns_to_scale"]}
    return scene([block("plotly_build", {"x": cd["K"], "y": cd["L"], "z": cd["Q"], "levels": cd["levels"], "x_title": "capital K",
                                         "y_title": "labour L", "path": [[p[0], p[1]] for p in cd["expansion_path"]], "path_label": "cheapest mix",
                                         "title": "A Cobb-Douglas production function", "subtitle": "isoquants by Plotly (contour) · the expansion path grows",
                                         "panel": ["Q = K^0.4 × L^0.6", f"α + β = 1: {cd['returns_to_scale']} returns to scale",
                                                   f"cheapest mix K/L = (α/β)(w/r) = {cd['k_over_l']:.2f}", "input prices r = 2, w = 1"],
                                         "badge": "computed by NumPy, drawn by Plotly"})], 4.2)


# ---------------------------------------------------------------- batch 3: law

def criminal_procedure(w: Work) -> dict:
    from . import sources
    from .adapters import law
    asset, act = sources.india_code_act(BNSS, w.library, opener=w.opener)
    steps = [{"id": "fir", "title": "Information in cognizable cases.", "label": "FIR: information to the police"},
             {"id": "inv", "title": "Procedure for investigation.", "label": "Investigation"},
             {"id": "report", "title": "Report of police officer on completion of investigation.", "label": "Police report"},
             {"id": "cog", "title": "Cognizance of offences by Magistrate.", "label": "Magistrate takes cognizance"},
             {"id": "open", "title": "Opening case for prosecution.", "label": "Sessions trial opens"},
             {"id": "q", "label": "Ground to proceed?", "kind": "decision"},
             {"id": "dis", "title": "Discharge.", "between": [248, 260], "label": "Discharge", "kind": "end"},
             {"id": "charge", "title": "Framing of charge.", "between": [248, 260], "label": "Charge framed"},
             {"id": "judg", "title": "Judgment of acquittal or conviction.", "label": "Judgment: acquittal or conviction", "kind": "end"}]
    edges = [["fir", "inv"], ["inv", "report"], ["report", "cog"], ["cog", "open"], ["open", "q"], ["q", "dis", "no"], ["q", "charge", "yes"],
             ["charge", "judg"]]
    flow = law.procedure(act, steps, edges)
    w.notes["india_code"] = {"act": act["title"], "sections": len(act["sections"]),
                             "steps": {n["id"]: n.get("section") for n in flow["nodes"] if n.get("section")}}
    panel = [{"node": n["id"], "tag": f"s. {n['section']}", "text": n["official_title"]} for n in flow["nodes"] if n.get("section")]
    return scene([block("flow_build", dict(flow, rankdir="TB", ranksep=30, wrap=26, seconds=3.3, section_prefix="Section ", panel=panel, panel_width=760,
                                           panel_title="the section titles, as India Code publishes them",
                                           title="A criminal case, from FIR to judgment (sessions trial)",
                                           subtitle=f"{act['title']} · section numbers read from India Code, laid out by dagre",
                                           badge=f"{len(act['sections'])} sections read from India Code"))], 4.2)


def case_card(w: Work) -> dict:
    from . import sources
    from .adapters import law
    asset, record = sources.sc_judgment(1973, r"KESAVANANDA BHARATI", w.library, opener=w.opener)
    card = law.case_card(record)
    w.notes["sc_judgments"] = {"bench": card["bench"], "decided": card["decided"], "citations": card["citations"]}
    return scene([block("case_card", {"card": card, "kind": "Supreme Court of India · judgment", "step_seconds": 0.4,
                                      "title": "A case card from the judgments dataset", "subtitle": "every field read from the record, none typed in",
                                      "credit": sources.SC_CREDIT})], 4.4)


def courts_tree(w: Work) -> dict:
    from . import sources
    from .adapters import law
    asset, act = sources.india_code_act(BNSS, w.library, opener=w.opener)
    section = law.find_section(act, "Classes of Criminal Courts.")
    classes = law.listed_items(section)
    w.notes["india_code_classes"] = {"section": section["number"], "classes": classes}
    root = {"name": "Supreme Court of India", "children": [{"name": "High Court",
            "children": [{"name": c, "note": f"BNSS s. {section['number']}"} for c in classes]}]}
    return scene([block("tree_build", {"root": root, "seconds": 2.6, "wrap": 20, "title": "Criminal courts in India",
                                       "subtitle": f"the classes of criminal courts listed in section {section['number']} of the BNSS (India Code), grown by D3",
                                       "badge": "D3 tree layout"})], 4.0)


# ---------------------------------------------------------------- batch 3: psychology, education, sociology

def stroop(w: Work) -> dict:
    from .adapters import behaviour
    data = behaviour.stroop(colours=("red", "green", "blue"), n_reps=1, seed=7)
    w.notes["psychopy"] = {"trials": len(data["trials"]), "congruent": data["congruent"], "designed_by": data["designed_by"]}
    return scene([block("experiment_flow", dict(data, seconds=3.4, title="The Stroop experiment, trial by trial",
                                                subtitle=f"trial list made by {data['designed_by']} · seed {data['seed']}",
                                                badge="name the ink colour, not the word"))], 4.2)


def teaching_method(w: Work) -> dict:
    from .adapters import behaviour
    fit = behaviour.teaching_method()
    w.notes["statsmodels_logit"] = {k: fit[k] for k in ("odds_ratio_psi", "odds_ratio_ci", "p_value_psi", "n")}
    return scene([block("xy_lines", {"series": [{"x": fit["gpa"], "y": fit["without_psi"], "label": "usual teaching", "start": 0.3, "seconds": 1.6},
                                                {"x": fit["gpa"], "y": fit["with_psi"], "label": "new method (PSI)", "start": 1.4, "seconds": 1.6}],
                                     "x_label": "grade point average", "y_label": "chance the grade improves", "y_domain": [0, 1],
                                     "title": "Does a new teaching method help?", "legend_box": True,
                                     "subtitle": f"logit model by {fit['fitted_by']} on {fit['n']} students (Spector and Mazzeo, 1980)",
                                     "note": f"PSI multiplies the odds by {fit['odds_ratio_psi']:.1f} (95% CI {fit['odds_ratio_ci'][0]:.1f} to "
                                             f"{fit['odds_ratio_ci'][1]:.0f}), p = {fit['p_value_psi']:.3f}"})], 4.2)


def brain_lobes(w: Work) -> dict:
    from . import sources
    asset, info = sources.z_anatomy("NervousSystem100", ".", w.library, min_vertices=20, title="Brain by lobes",
                                    group=r"^(Frontal|Parietal|Temporal|Occipital) lobe\.g$|^Cerebellum\.g$|^Brainstem\.g$", opener=w.opener)
    w.notes["z_anatomy"] = {"objects": info["objects"], "parts": info["parts"], "names": info["names"]}
    parts = [{"match": "^Frontal[ _]lobe", "colour": "#4f8dff", "label": "frontal: planning, movement", "at": 0.5},
             {"match": "^Parietal[ _]lobe", "colour": "#3ddc84", "label": "parietal: touch, space", "at": 1.0},
             {"match": "^Temporal[ _]lobe", "colour": "#ffd23f", "label": "temporal: hearing, memory", "at": 1.5},
             {"match": "^Occipital[ _]lobe", "colour": "#ff7a50", "label": "occipital: vision", "at": 2.0},
             {"match": "^Cerebellum", "colour": "#c79bff", "label": "cerebellum: balance", "at": 2.5},
             {"match": "^Brainstem", "colour": "#ff5a8a", "label": "brainstem: breathing, heartbeat", "at": 3.0}]
    return scene([block("model_3d", {"src": w.src(asset), "title": "The brain, lobe by lobe", "parts": parts, "spin": True, "shift_x": -260,
                                     "subtitle": f"Z-Anatomy model · Blender joined {info['parts']} parts into {info['objects']} · three.js",
                                     "turn_degrees": -60, "start_degrees": 90, "seconds": 4.2, "distance": 3.4, "camera_height": 0.5,
                                     "credit": "Z-Anatomy · CC BY-SA 4.0 (share-alike)"}, box=FULL)], 4.2)


def learning_cycle(w: Work) -> dict:
    nodes = [{"id": "ce", "label": "Concrete experience"}, {"id": "ro", "label": "Reflective observation"},
             {"id": "ac", "label": "Abstract conceptualisation"}, {"id": "ae", "label": "Active experimentation"}]
    return scene([block("flow_build", {"nodes": nodes, "edges": [], "layout": "cycle", "seconds": 2.4, "wrap": 14,
                                       "centre": "Kolb (1984)", "title": "The experiential learning cycle",
                                       "subtitle": "four stages that repeat: BIE's flow block in its cycle layout"})], 4.0)


# ---------------------------------------------------------------- batch 3: languages and literature

def kinetic_sanskrit(w: Work) -> dict:
    from . import sources
    from .adapters import language
    font = sources.noto_devanagari(w.library, opener=w.opener)
    data = language.sentence("सर्वे भवन्तु सुखिनः सर्वे सन्तु निरामयाः ।", lang="sa",
                             glosses=["all", "may be", "happy", "all", "may be", "free from illness"])
    w.notes["indic_nlp"] = {"words": len(data["words"]), "aksharas": sum(len(x["aksharas"]) for x in data["words"]), "made_by": data["made_by"]}
    return scene([block("kinetic_text", dict(data, font_src=w.src(font), seconds=3.3, title="A Sanskrit line, word by word",
                                             subtitle=data["made_by"], translation="May all be happy; may all be free from illness.",
                                             credit=font.credit))], 4.2)


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
    # batch 2
    Demo("elec-rc-circuit", 2, "An RC circuit drawn by schemdraw, simulated by ngspice, solved by lcapy",
         ("schemdraw", "ngspice", "lcapy", "katex", "d3", "bie-science-blocks"), ("circuit_diagram", "signal_plot"), 4.6, rc_circuit),
    Demo("elec-step-response", 2, "Step responses for three damping ratios (python-control, checked by scipy.signal)",
         ("python-control", "scipy-signal", "katex", "d3", "bie-science-blocks"), ("signal_plot",), 4.2, step_response),
    Demo("mech-beam", 2, "A loaded steel beam bends (PyNite, checked by sympy.physics)", ("pynite", "sympy-physics", "bie-science-blocks"),
         ("structure_load",), 4.0, beam),
    Demo("mech-flange", 2, "A pipe flange built by CadQuery, turning in three.js", ("cadquery", "trimesh", *THREE_STACK), ("machine_part_3d",), 4.0, flange),
    Demo("mech-rankine", 2, "A Rankine steam cycle on a T-s chart from CoolProp", ("coolprop", "d3", "bie-science-blocks"), ("function_graph",), 4.2, rankine_cycle),
    Demo("mech-heat-plate", 2, "Heat flow in a plate by scikit-fem", ("scikit-fem", "d3", "bie-science-blocks"), ("vector_field",), 4.0, heat_plate),
    Demo("geo-relief", 2, "Himalaya relief and profile by PyGMT", ("pygmt", "gmt", "gmt-earth-relief", "bie-blocks", "d3", "bie-science-blocks"),
         ("terrain_or_layers", "map_region"), 4.2, relief),
    Demo("geo-seismic-rays", 2, "Seismic rays through the Earth's layers by ObsPy TauP", ("obspy", "bie-science-blocks"),
         ("earthquake_waves", "terrain_or_layers"), 4.2, seismic_rays),
    Demo("geo-quake-map", 2, "2025's strong earthquakes from the USGS on a Natural Earth map", ("usgs-earthquakes", "natural-earth", "topojson-client", "d3", "bie-science-blocks"),
         ("map_region",), 4.2, quake_map),
    Demo("geo-plates", 2, "Continents drifting over 200 million years by pyGPlates", ("pygplates", "gplates-muller2019", "d3", "bie-science-blocks"),
         ("plate_motion",), 4.2, plates),
    Demo("astro-orbits", 2, "The inner planets' orbits from JPL DE421 (Skyfield, Astropy)", ("skyfield", "astropy", "jpl-de421", "d3", "bie-science-blocks"),
         ("orbit_motion",), 4.2, planet_orbits),
    Demo("astro-sky", 2, "The night sky over New Delhi from the Hipparcos catalogue (Skyfield)", ("skyfield", "astropy", "hipparcos", "jpl-de421", "bie-science-blocks"),
         ("sky_map",), 4.0, night_sky),
    Demo("astro-earthrise", 2, "Earthrise from NASA's image library, zoom and focus", ("nasa-images", "bie-blocks"), ("focus_glow",), 4.2, earthrise),
    Demo("aero-aircraft", 2, "A trainer aircraft and its lift curve from AeroSandbox", ("aerosandbox", "trimesh", *THREE_STACK, "d3", "bie-science-blocks"),
         ("aircraft_shape",), 4.2, aircraft),
    Demo("aero-climb", 2, "A Cessna 172 climb simulated by JSBSim", ("jsbsim", "d3", "bie-science-blocks"), ("flight_motion",), 4.2, climb),
    # batch 3: social sciences, commerce, law, behaviour, language
    Demo("geo-india-state", 3, "Uttar Pradesh on India's map (Natural Earth, Shapely, d3-geo)", ("natural-earth-vector", "shapely", "d3", "bie-social-blocks"),
         ("map_region",), 4.2, india_state),
    Demo("hist-gt-road", 3, "The Grand Trunk Road drawn town by town", ("natural-earth-vector", "shapely", "d3", "bie-social-blocks"),
         ("map_route",), 4.2, gt_road),
    Demo("hist-timeline", 3, "Towards independence, 1857 to 1950, on a D3 time scale", ("d3", "bie-social-blocks"), ("timeline",), 4.2, national_movement),
    Demo("polity-bill-mermaid", 3, "How a Bill becomes an Act, in Mermaid with the ELK layout", ("mermaid", "mermaid-layout-elk", "elkjs", "bie-social-blocks"),
         ("flowchart",), 4.2, bill_to_act),
    Demo("hist-archive-images", 3, "The Salt March from Wikimedia Commons and Openverse", ("wikimedia-commons", "openverse", "bie-blocks"),
         ("focus_glow",), 4.2, archive_images),
    Demo("econ-growth-chartjs", 3, "India's GDP growth from the World Bank in Chart.js", ("world-bank", "chartjs", "bie-social-blocks"),
         ("chart_bar_line_pie",), 4.2, gdp_growth),
    Demo("econ-wealth-health-vega", 3, "Wealth and health of eight countries in Vega-Lite", ("world-bank", "vega-lite", "vega", "bie-social-blocks"),
         ("chart_bar_line_pie",), 4.2, wealth_health),
    Demo("econ-cobb-douglas-plotly", 3, "A Cobb-Douglas production function in Plotly", ("numpy", "plotly", "bie-social-blocks"),
         ("function_graph",), 4.2, cobb_douglas),
    Demo("law-procedure-flow", 3, "A criminal case from FIR to judgment, sections from India Code", ("india-code", "dagre", "bie-social-blocks"),
         ("flowchart",), 4.2, criminal_procedure),
    Demo("law-case-card", 3, "Kesavananda Bharati v. State of Kerala as a case card", ("sc-judgments", "pyarrow", "bie-social-blocks"),
         ("case_card",), 4.4, case_card),
    Demo("law-courts-tree", 3, "Classes of criminal courts (BNSS s. 6) as a tree", ("india-code", "d3", "bie-social-blocks"),
         ("tree_hierarchy",), 4.0, courts_tree),
    Demo("psy-stroop-flow", 3, "The Stroop experiment designed by PsychoPy", ("psychopy", "bie-social-blocks"), ("flowchart",), 4.2, stroop),
    Demo("edu-teaching-logit", 3, "A teaching method's effect by statsmodels (logit)", ("statsmodels", "d3", "bie-science-blocks"),
         ("function_graph", "chart_bar_line_pie"), 4.2, teaching_method),
    Demo("psy-brain-lobes", 3, "The brain lobe by lobe (Z-Anatomy, Blender, three.js)", ("z-anatomy", "blender", *THREE_STACK),
         ("anatomy_3d",), 4.2, brain_lobes),
    Demo("edu-learning-cycle", 3, "Kolb's learning cycle as a process cycle", ("bie-social-blocks",), ("process_cycle",), 4.0, learning_cycle),
    Demo("lang-kinetic-sanskrit", 3, "A Sanskrit line word by word in Devanagari and Roman", ("indic-nlp", "indic-transliteration", "noto-devanagari", "bie-social-blocks"),
         ("text_kinetic",), 4.2, kinetic_sanskrit),
)


def by_id(demo_id: str) -> Demo:
    for d in DEMOS:
        if d.id == demo_id:
            return d
    raise KeyError(demo_id)
