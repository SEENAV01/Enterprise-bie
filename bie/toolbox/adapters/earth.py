"""Earth science computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``relief``: a shaded relief map of a region drawn by PyGMT (GMT 6) from the SRTM15+ global relief grid (fetched once
  into GMT's own cache, ``GMT_USERDIR``), plus an elevation profile along a line (GMT's project + grdtrack).
- ``ray_paths``: seismic rays from an earthquake through the IASP91 Earth model by ObsPy's TauP, with arrival times,
  and the depths of the Earth's main layers.
- ``seismogram``: ObsPy's own example recording (three components), filtered, for a block to draw.
- ``reconstruct``: coastlines moved back in time by pyGPlates with a published plate model (rotation file and
  coastlines from the asset cache), simplified for drawing.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from .base import clean, need, need_program

EARTH_RELIEF = {"name": "SRTM15+ V2.7 global relief (Tozer et al., 2019), through GMT's remote data server",
                "licence": "free to use with citation (Scripps Institution of Oceanography); GMT remote data",
                "source": "https://www.generic-mapping-tools.org/remote-datasets/earth-relief.html"}


def _gmt_userdir(cache: Path | None = None) -> Path:
    from ..sources import cache_dir
    folder = Path(cache or cache_dir()) / "gmt"
    folder.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("GMT_USERDIR", str(folder))
    return folder


# GMT's messages when its remote data server could not be reached: after one failed fetch GMT turns remote downloads off
# for the rest of that session, so the next attempt opens a new session.
REMOTE_FAILURES = ("Remote download is currently deactivated", "Unable to obtain remote file", "Unable to get remote file",
                   "Libcurl Error", "remote data will be unavailable")


def load_relief(pygmt, *, resolution: str, region, tries: int = 3, wait: float = 20.0, sleep=time.sleep):
    """SRTM15+ through GMT's remote data server, asked again (in a new GMT session, after ``wait`` seconds, then twice
    that) when the server could not be reached; any other error, or the last failure, is raised with every attempt."""
    seen = []
    for attempt in range(tries):
        try:
            return pygmt.datasets.load_earth_relief(resolution=resolution, region=list(region), registration="gridline")
        except Exception as exc:
            text = str(exc)
            if not any(m in text for m in REMOTE_FAILURES):
                raise
            seen.append(text.strip().splitlines()[0][:200] if text.strip() else type(exc).__name__)
            if attempt < tries - 1:
                sleep(wait * (2 ** attempt))
    raise RuntimeError(f"GMT's remote data server could not be reached in {tries} attempts: " + " | ".join(seen))


def relief(region=(70.0, 100.0, 20.0, 40.0), out_png: str | Path = "relief.png", *, resolution: str = "02m",
           profile=((77.0, 22.0), (90.0, 36.0)), step_km: float = 10.0, width_cm: float = 16.0, dpi: int = 150, grid=None) -> dict:
    """``grid`` (an xarray grid of heights in metres) replaces the SRTM15+ download, for tests or a model's own data."""
    need_program("gmt")
    _gmt_userdir()
    pygmt = need("pygmt")
    if grid is None:
        grid = load_relief(pygmt, resolution=resolution, region=region)
    fig = pygmt.Figure()
    fig.grdimage(grid=grid, projection=f"M{width_cm}c", cmap="geo", shading=True, frame=False)
    fig.savefig(str(out_png), dpi=dpi)
    track = pygmt.project(center=list(profile[0]), endpoint=list(profile[1]), generate=step_km, unit=True)
    prof = pygmt.grdtrack(grid=grid, points=track[["r", "s", "p"]], newcolname="z")
    return clean({"png": str(out_png), "region": list(region), "min_m": float(grid.min()), "max_m": float(grid.max()),
                  "profile": {"lon": prof["r"].to_numpy(), "lat": prof["s"].to_numpy(), "km": prof["p"].to_numpy(),
                              "elevation_m": prof["z"].to_numpy(), "from": list(profile[0]), "to": list(profile[1])},
                  "data": EARTH_RELIEF, "drawn_by": f"PyGMT {pygmt.__version__} (GMT {pygmt.__gmt_version__ if hasattr(pygmt, '__gmt_version__') else '6'})"}, 3)


def ray_paths(distance_deg: float = 70.0, depth_km: float = 15.0, phases=("P", "S", "PcP", "PKP", "SKS"), *,
              model: str = "iasp91", max_points: int = 160) -> dict:
    np = need("numpy")
    need("obspy")
    from obspy.taup import TauPyModel
    taup = TauPyModel(model)
    arrivals = taup.get_ray_paths(source_depth_in_km=depth_km, distance_in_degree=distance_deg, phase_list=list(phases))
    radius = 6371.0
    rays, seen = [], set()
    for arrival in arrivals:
        if arrival.name in seen:                       # the first arrival of each phase is enough to draw
            continue
        seen.add(arrival.name)
        path = arrival.path
        keep = np.linspace(0, len(path) - 1, min(max_points, len(path))).astype(int)
        rays.append({"phase": arrival.name, "time_s": float(arrival.time), "angle_rad": path["dist"][keep],
                     "radius_km": radius - path["depth"][keep]})
    layers = [{"name": "crust", "top_km": 0, "radius_km": radius}, {"name": "mantle", "top_km": 35, "radius_km": radius - 35},
              {"name": "outer core", "top_km": 2889, "radius_km": radius - 2889},
              {"name": "inner core", "top_km": 5153.5, "radius_km": radius - 5153.5}]
    return clean({"distance_deg": distance_deg, "depth_km": depth_km, "model": model, "rays": rays, "layers": layers,
                  "earth_radius_km": radius, "computed_by": "ObsPy TauP"}, 3)


def seismogram(*, points: int = 900, freqmin: float = 1.0, freqmax: float = 10.0) -> dict:
    """ObsPy's bundled example recording (station BW.RJOB, three components), band-passed and resampled for drawing."""
    np = need("numpy")
    obspy = need("obspy")
    stream = obspy.read()                                # the example data shipped inside ObsPy
    stream.detrend("demean")
    stream.filter("bandpass", freqmin=freqmin, freqmax=freqmax)
    traces = []
    for trace in stream:
        data = trace.data.astype(float)
        idx = np.linspace(0, len(data) - 1, points).astype(int)
        peak = float(np.max(np.abs(data))) or 1.0
        traces.append({"channel": trace.id, "values": data[idx] / peak})
    first = stream[0]
    return clean({"start": str(first.stats.starttime), "seconds": float(first.stats.npts / first.stats.sampling_rate),
                  "traces": traces, "station": f"{first.stats.network}.{first.stats.station}",
                  "source": "ObsPy example data (obspy.read() with no file)", "processed_by": f"ObsPy {obspy.__version__}"}, 4)


def _simplify(points, min_step_deg: float):
    out = [points[0]]
    for lat, lon in points[1:]:
        if abs(lat - out[-1][0]) + abs(lon - out[-1][1]) >= min_step_deg:
            out.append((lat, lon))
    return out


def reconstruct(rotation_file: str | Path, coastline_file: str | Path, ages=tuple(range(200, -1, -10)), *,
                min_step_deg: float = 0.8, min_points: int = 5) -> dict:
    """Coastline polygons (lon, lat lists) at each age in million years, by pyGPlates."""
    pygplates = need("pygplates")
    rotations = pygplates.RotationModel(str(rotation_file))
    coastlines = pygplates.FeatureCollection(str(coastline_file))
    frames = []
    for age in ages:
        reconstructed = []
        pygplates.reconstruct(coastlines, rotations, reconstructed, float(age))
        shapes = []
        for item in reconstructed:
            points = item.get_reconstructed_geometry().to_lat_lon_list()
            if len(points) < min_points:
                continue
            simple = _simplify(points, min_step_deg)
            if len(simple) >= min_points:
                shapes.append([[round(lon, 2), round(lat, 2)] for lat, lon in simple])
        frames.append({"age_ma": age, "shapes": shapes, "points": sum(len(s) for s in shapes)})
    return {"frames": frames, "ages": list(ages), "reconstructed_by": f"pyGPlates {pygplates.__version__}"}
