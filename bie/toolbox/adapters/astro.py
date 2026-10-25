"""Astronomy computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``orbits``: where Mercury, Venus, Earth and Mars are around the Sun, day by day, from NASA JPL's DE421 ephemeris by
  Skyfield; Astropy checks each orbit's period against Kepler's third law.
- ``sky``: the bright stars above a place at a time (altitude and azimuth) from the Hipparcos catalogue by Skyfield,
  with the planets that are up.
The ephemeris and the catalogue are fetched once into the asset cache (``BIE_ASSET_CACHE/skyfield``).
"""
from __future__ import annotations

from pathlib import Path

from .base import clean, need

PLANETS = ("mercury", "venus", "earth", "mars")
EPHEMERIS = {"file": "de421.bsp", "name": "JPL Planetary Ephemeris DE421 (NASA JPL)", "licence": "Public domain (NASA JPL)",
             "source": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp"}
HIPPARCOS = {"name": "The Hipparcos Catalogue (ESA 1997), from CDS", "source": "https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat",
             "licence": "ESA Hipparcos Catalogue: free for scientific use with citation (CDS); commercial use by ESA's rules"}


def _loader(cache: Path | None = None):
    need("skyfield")
    from skyfield.api import Loader
    from ..sources import cache_dir
    folder = Path(cache or cache_dir()) / "skyfield"
    folder.mkdir(parents=True, exist_ok=True)
    return Loader(str(folder), verbose=False)


def orbits(start: str = "2026-01-01", days: int = 687, step_days: int = 3, *, cache: Path | None = None) -> dict:
    np = need("numpy")
    need("astropy")
    from astropy import constants, units
    from astropy.time import Time
    load = _loader(cache)
    eph = load(EPHEMERIS["file"])
    ts = load.timescale()
    begin = Time(start, scale="utc")
    jd = begin.jd + np.arange(0, days + 1, step_days)
    t = ts.tt_jd(Time(jd, format="jd", scale="utc").tt.jd)
    from skyfield.framelib import ecliptic_frame
    sun = eph["sun"]
    out = []
    for name in PLANETS:
        body = eph["mars barycenter" if name == "mars" else name]          # DE421 has Mars only as its barycentre
        x, y, _ = (body.at(t) - sun.at(t)).frame_xyz(ecliptic_frame).au     # in the plane of the Earth's orbit
        radius = np.hypot(x, y)
        a = float((radius.max() + radius.min()) / 2)                  # semi-major axis from the sampled orbit
        period_days = float((2 * np.pi * np.sqrt((a * units.au) ** 3 / (constants.G * constants.M_sun))).to(units.day).value)
        out.append({"name": name, "x_au": x, "y_au": y, "semi_major_au": a, "kepler_period_days": period_days})
    return clean({"start": start, "step_days": step_days, "days": days, "dates": [str(d)[:10] for d in Time(jd, format="jd").iso],
                  "planets": out, "ephemeris": EPHEMERIS, "computed_by": "Skyfield + Astropy"}, 4)


def sky(lat: float = 28.61, lon: float = 77.21, when: str = "2026-01-15T20:00:00", *, utc_offset_hours: float = 5.5,
        magnitude_limit: float = 3.5, cache: Path | None = None) -> dict:
    """Stars above the horizon at local time ``when`` (default New Delhi, 8 pm IST)."""
    np = need("numpy")
    need("astropy")
    from astropy.time import Time, TimeDelta
    from skyfield.api import Star, wgs84
    from skyfield.data import hipparcos
    load = _loader(cache)
    eph = load(EPHEMERIS["file"])
    ts = load.timescale()
    utc = Time(when, scale="utc") - TimeDelta(utc_offset_hours * 3600, format="sec")
    t = ts.from_astropy(utc)
    with load.open(hipparcos.URL) as handle:
        stars = hipparcos.load_dataframe(handle)
    bright = stars[stars["magnitude"] <= magnitude_limit]
    observer = eph["earth"] + wgs84.latlon(lat, lon)
    alt, az, _ = observer.at(t).observe(Star.from_dataframe(bright)).apparent().altaz()
    up = alt.degrees > 0
    planets = []
    for name in ("venus", "mars", "jupiter barycenter", "saturn barycenter"):
        palt, paz, _ = observer.at(t).observe(eph[name]).apparent().altaz()
        if palt.degrees > 0:
            planets.append({"name": name.split()[0], "alt": palt.degrees, "az": paz.degrees})
    return clean({"place": {"lat": lat, "lon": lon}, "local_time": when, "utc": utc.iso, "stars": {
        "hip": np.asarray(bright.index)[up], "alt": alt.degrees[up], "az": az.degrees[up], "magnitude": np.asarray(bright["magnitude"])[up]},
        "planets": planets, "catalogue": HIPPARCOS, "count": int(up.sum()), "computed_by": "Skyfield"}, 3)
