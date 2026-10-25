"""Mechanical and civil engineering computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``beam_point_load``: a simply supported beam with a point load, solved by PyNite (finite elements) and checked against
  the closed form from SymPy's ``sympy.physics.continuum_mechanics`` Beam; deflection and bending moment along it.
- ``flange_glb``: a pipe flange with bolt holes built by CadQuery (a real CAD kernel, OpenCascade), as a .glb for the
  3D blocks, with its volume and mass.
- ``rankine``: a steam Rankine cycle from CoolProp's water properties: the saturation dome and the four states on a
  temperature–entropy chart, with the cycle's efficiency.
- ``heated_plate``: steady heat flow in a square plate with one hot edge, by scikit-fem (finite elements): temperature
  at every mesh node and the heat-flux arrows.
"""
from __future__ import annotations

import tempfile
from pathlib import Path

from .base import clean, need


def beam_point_load(length: float = 6.0, load: float = 20e3, at: float = 2.0, *, E: float = 200e9, I: float = 8.36e-5,
                    points: int = 61) -> dict:
    np = need("numpy")
    pynite = need("pynite")
    need("sympy-physics")
    import sympy
    from sympy.physics.continuum_mechanics.beam import Beam

    model = pynite.FEModel3D()
    model.add_node("A", 0, 0, 0)
    model.add_node("B", length, 0, 0)
    model.add_material("Steel", E, 77e9, 0.3, 7850)
    model.add_section("Section", 0.0053, 3.9e-6, I, 1e-7)
    model.add_member("M", "A", "B", "Steel", "Section")
    model.def_support("A", True, True, True, True, False, False)        # pin
    model.def_support("B", False, True, True, False, False, False)      # roller
    model.add_member_pt_load("M", "Fy", -load, at)
    model.analyze(check_statics=False)
    member = model.members["M"]
    xs = np.linspace(0.0, length, points)
    deflection = np.array([member.deflection("dy", float(x)) for x in xs])
    moment = np.array([-member.moment("Mz", float(x)) for x in xs])      # sagging positive, as the textbooks draw it

    x = sympy.symbols("x")
    beam = Beam(length, E, I, variable=x)
    r1, r2 = sympy.symbols("R1 R2")
    beam.apply_load(r1, 0, -1)
    beam.apply_load(r2, length, -1)
    beam.apply_load(load, at, -1)
    beam.bc_deflection = [(0, 0), (length, 0)]
    beam.solve_for_reaction_loads(r1, r2)
    exact = sympy.lambdify(x, beam.deflection(), "numpy")
    exact_values = -np.array([float(exact(float(v))) for v in xs])      # SymPy's sign: downward loads give positive values
    fem_max = float(np.min(deflection))
    sym_max = float(np.min(exact_values))
    return clean({"x": xs, "deflection_m": deflection, "moment_Nm": moment, "length": length, "load_N": load, "at": at,
                  "max_deflection_mm": fem_max * 1000, "max_moment_kNm": float(np.max(moment)) / 1000,
                  "reactions_N": [float(beam.reaction_loads[r1]), float(beam.reaction_loads[r2])],
                  "sympy_max_deflection_mm": sym_max * 1000, "agree": abs(fem_max - sym_max) <= 0.01 * abs(sym_max),
                  "solved_by": "PyNite (finite elements)", "checked_by": "sympy.physics.continuum_mechanics.Beam"}, 6)


def flange_glb(outer: float = 120.0, thickness: float = 16.0, bore: float = 50.0, hub: float = 70.0, hub_height: float = 30.0,
               bolts: int = 6, bolt_circle: float = 95.0, bolt_hole: float = 12.0, density_kg_m3: float = 7850.0):
    """A flange in millimetres; returns (glb bytes, facts)."""
    cq = need("cadquery")
    trimesh = need("trimesh")
    body = (cq.Workplane("XY").circle(outer / 2).extrude(thickness)
            .faces(">Z").workplane().circle(hub / 2).extrude(hub_height)
            .faces(">Z").workplane().hole(bore)
            .faces("<Z").workplane().polarArray(bolt_circle / 2, 0, 360, bolts).hole(bolt_hole))
    volume_mm3 = body.val().Volume()
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / "flange.stl"
        cq.exporters.export(body, str(stl), tolerance=0.05, angularTolerance=0.1)
        mesh = trimesh.load(stl, file_type="stl")
    mesh.apply_translation(-mesh.bounding_box.centroid)
    mesh.apply_scale(2.0 / max(mesh.extents))
    mesh.apply_transform(trimesh.transformations.rotation_matrix(-1.5707963, [1, 0, 0]))   # CAD Z-up → glTF Y-up
    data = mesh.export(file_type="glb")
    return data, clean({"volume_cm3": volume_mm3 / 1000, "mass_kg": volume_mm3 * 1e-9 * density_kg_m3, "faces": len(mesh.faces),
                        "bolts": bolts, "built_by": f"CadQuery {cq.__version__} (OpenCascade)"})


def rankine(p_high_bar: float = 80.0, p_low_bar: float = 0.1, t_turbine_c: float = 480.0, *, dome_points: int = 60) -> dict:
    """Ideal Rankine cycle on a T–s chart: 1 pump inlet (saturated liquid), 2 pump outlet, 3 turbine inlet, 4 turbine outlet."""
    np = need("numpy")
    coolprop = need("coolprop")
    from CoolProp.CoolProp import PropsSI
    fluid = "Water"
    ph, pl, t3 = p_high_bar * 1e5, p_low_bar * 1e5, t_turbine_c + 273.15
    s1, h1 = PropsSI("S", "P", pl, "Q", 0, fluid), PropsSI("H", "P", pl, "Q", 0, fluid)
    t1 = PropsSI("T", "P", pl, "Q", 0, fluid)
    h2 = PropsSI("H", "P", ph, "S", s1, fluid)
    t2 = PropsSI("T", "P", ph, "S", s1, fluid)
    h3, s3 = PropsSI("H", "P", ph, "T", t3, fluid), PropsSI("S", "P", ph, "T", t3, fluid)
    h4, t4 = PropsSI("H", "P", pl, "S", s3, fluid), PropsSI("T", "P", pl, "S", s3, fluid)
    efficiency = ((h3 - h4) - (h2 - h1)) / (h3 - h2)
    t_crit = PropsSI("Tcrit", fluid)
    temps = np.linspace(PropsSI("Ttriple", fluid) + 0.01, t_crit - 0.05, dome_points)
    dome_l = [PropsSI("S", "T", t, "Q", 0, fluid) for t in temps]
    dome_v = [PropsSI("S", "T", t, "Q", 1, fluid) for t in temps]
    # the heating line 2 → 3 at constant pressure, sampled so it bends along the dome and into superheat
    heat_t = np.linspace(t2, t3, 40)
    heat_s = []
    t_sat_high = PropsSI("T", "P", ph, "Q", 0, fluid)
    for t in heat_t:
        if abs(t - t_sat_high) < 0.05:
            heat_s.append(PropsSI("S", "P", ph, "Q", 0, fluid))
        else:
            heat_s.append(PropsSI("S", "P", ph, "T", t, fluid))
    heat_s.insert(int(np.searchsorted(heat_t, t_sat_high)), PropsSI("S", "P", ph, "Q", 1, fluid))
    heat_t = np.insert(heat_t, int(np.searchsorted(heat_t, t_sat_high)), t_sat_high)
    k = 1 / 1000
    states = [{"name": "1", "T_C": t1 - 273.15, "s": s1 * k}, {"name": "2", "T_C": t2 - 273.15, "s": s1 * k},
              {"name": "3", "T_C": t3 - 273.15, "s": s3 * k}, {"name": "4", "T_C": t4 - 273.15, "s": s3 * k}]
    return clean({"dome": {"s_liquid": np.array(dome_l) * k, "s_vapour": np.array(dome_v) * k, "T_C": temps - 273.15},
                  "heating": {"s": np.array(heat_s) * k, "T_C": heat_t - 273.15}, "states": states, "efficiency": efficiency,
                  "p_high_bar": p_high_bar, "p_low_bar": p_low_bar, "computed_by": f"CoolProp {coolprop.__version__}"})


def heated_plate(*, refine: int = 5, hot: float = 100.0, cold: float = 20.0, arrows: int = 9) -> dict:
    """Laplace's equation on the unit square: a hot strip on the left edge (0.35 ≤ y ≤ 0.65), the right edge cold, every
    other edge insulated, so heat spreads out from the strip and the flux arrows fan out."""
    np = need("numpy")
    skfem = need("scikit-fem")
    from skfem.models.poisson import laplace
    mesh = skfem.MeshTri().refined(refine)
    basis = skfem.Basis(mesh, skfem.ElementTriP1())
    A = laplace.assemble(basis)
    hot_dofs = basis.get_dofs(lambda x: np.isclose(x[0], 0.0) & (x[1] >= 0.35) & (x[1] <= 0.65)).all()
    cold_dofs = basis.get_dofs(lambda x: np.isclose(x[0], 1.0)).all()
    u = np.zeros(basis.N)
    u[hot_dofs], u[cold_dofs] = hot, cold
    temperature = skfem.solve(*skfem.condense(A, np.zeros(basis.N), x=u, D=np.concatenate([hot_dofs, cold_dofs])))

    def at(px, py):
        return basis.probes(np.array([px, py])) @ temperature

    grid = np.linspace(0.08, 0.92, arrows)
    px, py = np.array([[x, y] for y in grid for x in grid]).T
    h = 0.01                                           # flux = −k ∇T (k = 1), by central differences of the FE field
    fx = -(at(px + h, py) - at(px - h, py)) / (2 * h)
    fy = -(at(px, py + h) - at(px, py - h)) / (2 * h)
    return clean({"nodes": mesh.p.T, "triangles": mesh.t.T, "temperature": temperature,
                  "arrows": {"x": px, "y": py, "fx": fx, "fy": fy}, "hot": hot, "cold": cold, "elements": mesh.t.shape[1],
                  "solved_by": f"scikit-fem {skfem.__version__}"}, 3)
