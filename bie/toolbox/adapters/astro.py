"""Astronomy computed in Python for BIE's web blocks to draw (Task 046a, batch 2).

- ``orbits``: where Mercury, Venus, Earth and Mars are around the Sun, day by day, from NASA JPL's DE421 ephemeris by
  Skyfield; Astropy checks each orbit's period against Kepler's third law.
- ``sky``: the bright stars above a place at a time (altitude and azimuth) by Skyfield, with the planets that are up.
  The default star source is the Yale Bright Star Catalogue (public domain; Navin, 29 October 2026: Hipparcos stays out
  of lessons until ESA's commercial terms are checked); ``catalogue="hipparcos"`` still reads the Hipparcos file.
The ephemeris and the catalogues are fetched once into the asset cache (``BIE_ASSET_CACHE/skyfield``).
"""
from __future__ import annotations

import gzip
import urllib.request
from pathlib import Path

from .base import clean, need

PLANETS = ("mercury", "venus", "earth", "mars")
EPHEMERIS = {"file": "de421.bsp", "name": "JPL Planetary Ephemeris DE421 (NASA JPL)", "licence": "Public domain (NASA JPL)",
             "source": "https://naif.jpl.nasa.gov/pub/naif/generic_kernels/spk/planets/a_old_versions/de421.bsp"}
HIPPARCOS = {"name": "The Hipparcos Catalogue (ESA 1997), from CDS", "source": "https://cdsarc.cds.unistra.fr/ftp/cats/I/239/hip_main.dat",
             "licence": "ESA Hipparcos Catalogue: free for scientific use with citation (CDS); commercial use by ESA's rules",
             # VizieR mirrors of the same file (I/239/hip_main.dat, 53,316,318 bytes, 24 June 1997), tried in this order when CDS
             # does not answer (F-16, 27 October 2026: CDS was down for hours; the CfA mirror answered)
             "mirrors": ("https://vizier.cfa.harvard.edu/ftp/cats/I/239/hip_main.dat", "https://vizier.iucaa.in/ftp/cats/I/239/hip_main.dat",
                         "https://vizier.nao.ac.jp/ftp/cats/I/239/hip_main.dat")}
BSC = {"name": "Yale Bright Star Catalogue, 5th revised edition (Hoffleit & Warren 1991), from the Harvard-Smithsonian CfA",
       "file": "bsc5.dat.gz", "source": "https://vizier.cfa.harvard.edu/ftp/cats/V/50/catalog.gz",
       # the same V/50 file from CDS and its mirrors, then the CfA's own copy (http), tried in this order when a server does not answer
       "mirrors": ("https://cdsarc.cds.unistra.fr/ftp/cats/V/50/catalog.gz", "https://vizier.iucaa.in/ftp/cats/V/50/catalog.gz",
                   "http://tdc-www.harvard.edu/catalogs/bsc5.dat.gz"),
       "licence": "Public domain (the Bright Star Catalogue is distributed without restriction by CDS V/50 and the CfA; Navin, 29 October 2026)",
       "epoch": 2000.0}
# BSC5 fixed-width columns (1-based bytes of the V/50 ReadMe): HR 1-4, Name 5-14, RA J2000 76-83 (h, m, s), Dec J2000 84-90
# (sign, d, m, s), Vmag 103-107, pmRA 149-154 and pmDE 155-160 (arcsec/yr). 14 of the 9,110 lines are novae or non-stars
# without a J2000 position and are skipped.
BSC_COLUMNS = {"hr": (0, 4), "name": (4, 14), "ra_h": (75, 77), "ra_m": (77, 79), "ra_s": (79, 83), "de_sign": (83, 84), "de_d": (84, 86),
               "de_m": (86, 88), "de_s": (88, 90), "vmag": (102, 107), "pm_ra": (148, 154), "pm_de": (154, 160)}


def _fetch_bsc(folder: Path) -> Path:
    """The Yale catalogue in the cache folder: ``bsc5.dat`` (plain) or ``bsc5.dat.gz``, fetched once from the CfA or CDS."""
    plain, packed = folder / "bsc5.dat", folder / BSC["file"]
    if plain.exists() and plain.stat().st_size > 0:
        return plain
    if packed.exists() and packed.stat().st_size > 0:
        return packed
    errors = []
    for url in (BSC["source"], *BSC["mirrors"]):
        try:
            with urllib.request.urlopen(url, timeout=120) as resp:      # noqa: S310 - a fixed list of catalogue mirrors
                data = resp.read()
            gzip.decompress(data)                                        # a whole, readable file or the next mirror
            tmp = packed.with_suffix(packed.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(packed)
            return packed
        except Exception as exc:                                         # noqa: BLE001 - every mirror is tried, then named
            errors.append(f"{url}: {exc}")
    raise RuntimeError("the Yale Bright Star Catalogue could not be fetched: " + "; ".join(errors))


def load_bsc(path: Path) -> list:
    """The Yale Bright Star Catalogue as plain rows (pure Python, no pandas): hr, name, ra_hours, dec_degrees, proper motion
    in mas/yr, parallax 0, epoch J2000, magnitude. ``bsc_frame`` turns them into the Skyfield star dataframe."""
    raw = path.read_bytes()
    text = (gzip.decompress(raw) if path.suffix == ".gz" else raw).decode("latin-1")
    rows = []
    c = BSC_COLUMNS

    def field(line, key):
        a, b = c[key]
        return line[a:b].strip()

    def number(line, key, default=0.0):
        value = field(line, key)
        return float(value) if value else default

    for line in text.splitlines():
        if len(line) < 107 or not field(line, "ra_h") or not field(line, "vmag"):
            continue
        ra_hours = number(line, "ra_h") + number(line, "ra_m") / 60 + number(line, "ra_s") / 3600
        dec = number(line, "de_d") + number(line, "de_m") / 60 + number(line, "de_s") / 3600
        if field(line, "de_sign") == "-":
            dec = -dec
        rows.append({"hr": int(field(line, "hr")), "name": field(line, "name"), "ra_hours": ra_hours, "dec_degrees": dec,
                     "ra_mas_per_year": number(line, "pm_ra") * 1000.0, "dec_mas_per_year": number(line, "pm_de") * 1000.0,
                     "parallax_mas": 0.0, "epoch_year": BSC["epoch"], "magnitude": number(line, "vmag")})
    return rows


def bsc_frame(rows: list):
    """The rows of ``load_bsc`` as a Skyfield star dataframe indexed by HR number (pandas, Skyfield's own dependency)."""
    import pandas as pd
    return pd.DataFrame(rows).set_index("hr")


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
        magnitude_limit: float = 3.5, cache: Path | None = None, catalogue: str = "bsc") -> dict:
    """Stars above the horizon at local time ``when`` (default New Delhi, 8 pm IST) from the Yale Bright Star Catalogue
    (``catalogue="bsc"``, the default) or the Hipparcos catalogue (``"hipparcos"``, internal proofs only)."""
    np = need("numpy")
    need("astropy")
    from astropy.time import Time, TimeDelta
    from skyfield.api import Star, wgs84
    load = _loader(cache)
    eph = load(EPHEMERIS["file"])
    ts = load.timescale()
    utc = Time(when, scale="utc") - TimeDelta(utc_offset_hours * 3600, format="sec")
    t = ts.from_astropy(utc)
    if catalogue == "hipparcos":
        from skyfield.data import hipparcos
        with load.open(hipparcos.URL) as handle:
            stars = hipparcos.load_dataframe(handle)
        source = HIPPARCOS
    elif catalogue == "bsc":
        stars = bsc_frame(load_bsc(_fetch_bsc(Path(load.directory))))
        source = BSC
    else:
        raise ValueError(f"catalogue must be bsc or hipparcos, not {catalogue!r}")
    bright = stars[stars["magnitude"] <= magnitude_limit]
    observer = eph["earth"] + wgs84.latlon(lat, lon)
    alt, az, _ = observer.at(t).observe(Star.from_dataframe(bright)).apparent().altaz()
    up = alt.degrees > 0
    planets = []
    for name in ("venus", "mars", "jupiter barycenter", "saturn barycenter"):
        palt, paz, _ = observer.at(t).observe(eph[name]).apparent().altaz()
        if palt.degrees > 0:
            planets.append({"name": name.split()[0], "alt": palt.degrees, "az": paz.degrees})
    ids = np.asarray(bright.index)[up]
    return clean({"place": {"lat": lat, "lon": lon}, "local_time": when, "utc": utc.iso, "stars": {
        "ids": ids, "id_kind": "hip" if catalogue == "hipparcos" else "hr", "hip": ids if catalogue == "hipparcos" else [],
        "alt": alt.degrees[up], "az": az.degrees[up], "magnitude": np.asarray(bright["magnitude"])[up]},
        "planets": planets, "catalogue": {k: v for k, v in source.items() if k != "mirrors"}, "count": int(up.sum()), "computed_by": "Skyfield"}, 3)
