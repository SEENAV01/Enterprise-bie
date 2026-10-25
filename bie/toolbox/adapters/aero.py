"""Aerospace computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``trainer_aircraft``: a small trainer aircraft defined in AeroSandbox (NACA 2412 wing, tail, fuselage), meshed to a
  .glb for the 3D blocks, with its lift curve from AeroSandbox's vortex lattice method.
- ``climb``: a Cessna 172 (JSBSim's c172x model and its own autopilot) climbing from 1,500 ft to 2,500 ft at full
  throttle and levelling off, sampled once a second.
"""
from __future__ import annotations

from .base import clean, need


def trainer_aircraft(alphas=(-4, 0, 4, 8, 12), *, velocity: float = 50.0):
    """Returns (glb bytes, facts with the lift curve)."""
    np = need("numpy")
    asb = need("aerosandbox")
    trimesh = need("trimesh")
    wing, tail = asb.Airfoil("naca2412"), asb.Airfoil("naca0010")
    plane = asb.Airplane(name="Trainer", xyz_ref=[0.4, 0, 0], wings=[
        asb.Wing(name="Main wing", symmetric=True, xsecs=[
            asb.WingXSec(xyz_le=[0, 0, 0], chord=1.6, twist=2, airfoil=wing),
            asb.WingXSec(xyz_le=[0.2, 5.0, 0.3], chord=1.0, twist=0, airfoil=wing)]),
        asb.Wing(name="Horizontal tail", symmetric=True, xsecs=[
            asb.WingXSec(xyz_le=[5.2, 0, 0.1], chord=0.9, twist=-2, airfoil=tail),
            asb.WingXSec(xyz_le=[5.5, 1.6, 0.1], chord=0.6, twist=-2, airfoil=tail)]),
        asb.Wing(name="Fin", xsecs=[
            asb.WingXSec(xyz_le=[5.1, 0, 0.1], chord=1.0, airfoil=tail),
            asb.WingXSec(xyz_le=[5.6, 0, 1.4], chord=0.6, airfoil=tail)])],
        fuselages=[asb.Fuselage(name="Fuselage", xsecs=[asb.FuselageXSec(xyz_c=[x, 0, 0], radius=r) for x, r in
                                                        [(-1.0, 0.05), (-0.6, 0.45), (0.5, 0.6), (2.5, 0.5), (5.0, 0.25), (6.0, 0.08)]])])
    points, quads = plane.mesh_body(method="tri")
    mesh = trimesh.Trimesh(vertices=np.asarray(points), faces=np.asarray(quads), process=True)
    mesh.apply_translation(-mesh.bounding_box.centroid)
    mesh.apply_scale(2.0 / max(mesh.extents))
    # AeroSandbox axes (x back, y right, z up) → glTF (x right, y up, z towards the viewer): nose points to −z
    mesh.apply_transform(np.array([[0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, 0], [0, 0, 0, 1]], dtype=float))
    curve = []
    for alpha in alphas:
        result = asb.VortexLatticeMethod(airplane=plane, op_point=asb.OperatingPoint(velocity=velocity, alpha=alpha),
                                         spanwise_resolution=6, chordwise_resolution=4).run()
        curve.append({"alpha_deg": alpha, "CL": float(result["CL"]), "CD_induced": float(result["CD"])})
    slope = (curve[-1]["CL"] - curve[0]["CL"]) / (alphas[-1] - alphas[0])
    return mesh.export(file_type="glb"), clean({
        "wing_area_m2": float(plane.s_ref), "span_m": float(plane.b_ref), "lift_curve": curve, "cl_per_degree": slope,
        "faces": len(mesh.faces), "airfoils": ["NACA 2412 (wing)", "NACA 0010 (tail)"],
        "built_by": f"AeroSandbox {asb.__version__} (vortex lattice method)"})


def climb(*, start_ft: float = 1500.0, target_ft: float = 2500.0, seconds: float = 120.0, climb_after: float = 10.0) -> dict:
    jsbsim = need("jsbsim")
    fdm = jsbsim.FGFDMExec(jsbsim.get_default_root_dir())
    fdm.set_debug_level(0)
    fdm.load_model("c172x")
    fdm.set_dt(1 / 120)
    fdm["ic/h-sl-ft"], fdm["ic/vc-kts"], fdm["ic/gamma-deg"], fdm["ic/psi-true-deg"] = start_ft, 90, 0, 90
    fdm.run_ic()
    fdm["propulsion/set-running"] = -1
    fdm["fcs/mixture-cmd-norm"], fdm["fcs/throttle-cmd-norm"] = 1.0, 0.7
    fdm.run()
    fdm["simulation/do_simple_trim"] = 1
    fdm["ap/attitude_hold"], fdm["ap/heading_setpoint"], fdm["ap/heading_hold"] = 1, 90, 1
    fdm["ap/altitude_setpoint"], fdm["ap/altitude_hold"] = start_ft, 1
    rows, steps = [], 0
    while fdm.get_sim_time() < seconds:
        if fdm.get_sim_time() >= climb_after:
            fdm["ap/altitude_setpoint"], fdm["fcs/throttle-cmd-norm"] = target_ft, 1.0
        fdm.run()
        steps += 1
        if steps % 120 == 0:
            rows.append((fdm.get_sim_time(), fdm["position/h-sl-ft"], fdm["velocities/vc-kts"], fdm["attitude/theta-deg"],
                         fdm["position/distance-from-start-mag-mt"], fdm["velocities/h-dot-fps"] * 60))
    columns = list(zip(*rows))
    best = max(r[5] for r in rows)
    return clean({"t_s": columns[0], "altitude_ft": columns[1], "airspeed_kts": columns[2], "pitch_deg": columns[3],
                  "distance_m": columns[4], "climb_fpm": columns[5], "best_climb_fpm": best, "start_ft": start_ft,
                  "target_ft": target_ft, "aircraft": "Cessna 172 (JSBSim c172x model)",
                  "simulated_by": f"JSBSim {jsbsim.__version__} (with the model's own autopilot)"}, 2)
