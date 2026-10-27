"""Asset sources of the toolbox (Task 046a): models, structures and pictures fetched on demand into BIE's asset
library (``bie.brain.assets.AssetLibrary``) with their licence, source page and credit. Nothing large goes into git:
big downloads (zip archives, FBX files) stay in a cache folder outside the repository (``BIE_ASSET_CACHE``, default
``~/.cache/bie/sources``) and only the file a video needs (a .glb, a .pdb, a .png) enters the library.

Licences are recorded as each source states them and read through the licence policy (``licence_policy.json``,
``bie.toolbox.licence``). Non-commercial and no-derivatives files are never fetched. Named Commons and Openverse
pictures (per-item sources) are fetched only when a lesson may use them. Files a lesson may not use (Z-Anatomy's
CC BY-SA models, sources waiting for Navin) can still be fetched for the toolbox's internal proofs; share-alike ones are
tagged "share-alike", and the lesson gate (``lesson_licence_check``) stops every one of them before a lesson is rendered.
Every fetch takes an ``opener`` so tests run offline.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import time
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from bie.brain.assets import TRANSIENT_HTTP, USER_AGENT, AssetLibrary, Candidate, commons_file, openverse_image as openverse_candidate
from bie.brain.assets import _open as open_url

from . import licence as policy

MAX_BYTES = 300 * 1024 * 1024
RCSB = "https://files.rcsb.org/download/{id}.pdb"
PUBCHEM = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/{name}/SDF?record_type={record}"
NIH_ENTRY = "https://3d.nih.gov/api/entries/{id}"
NIH_DOWNLOAD = "https://3d.nih.gov/api/download?submissionId={submission}&fileIds={file}"
SERVIER_FILE = "https://smart.servier.com/wp-content/uploads/{path}"
BP3D_BASE = "https://dbarchive.biosciencedbc.jp/data/bodyparts3d/LATEST/"
BP3D_ZIP = BP3D_BASE + "partof_BP3D_4.0_obj_99.zip"
BP3D_ELEMENTS = BP3D_BASE + "partof_element_parts.txt"
BP3D_CREDIT = "BodyParts3D, © The Database Center for Life Science licensed under CC Attribution 4.0 International"
ZANATOMY_FBX = "https://raw.githubusercontent.com/LluisV/Z-Anatomy/PC-Version/Resources/Models/FBX/{name}.fbx"
USGS_QUAKES = ("https://earthquake.usgs.gov/fdsnws/event/1/query?format=geojson&starttime={start}&endtime={end}"
               "&minmagnitude={magnitude}&orderby=time-asc")
GPLATES_MODELS = {"muller2019": {"base": "https://repo.gplates.org/webdav/pmm/muller2019/",
                                 "rotations": ("Rotations.zip", "Rotations/Muller_etal_2019_CombinedRotations.rot"),
                                 "coastlines": ("Coastlines.zip", "Coastlines/Muller_etal_2019_Global_Coastlines.gpmlz"),
                                 "credit": "Müller et al. (2019), Tectonics, plate model v2.0 (doi:10.5281/zenodo.11601026), CC BY 4.0",
                                 "licence": "CC BY 4.0"}}
NASA_SEARCH = "https://images-api.nasa.gov/search?nasa_id={id}&media_type=image"
NASA_ASSET = "https://images-api.nasa.gov/asset/{id}"
# batch 3: geography and history, economics, law, languages
NATURAL_EARTH = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/v5.1.2/geojson/{name}.geojson"
NATURAL_EARTH_FILES = {   # Natural Earth 5.1.2 (tag commit f1890d9f), public domain; pinned by content hash
    "ne_10m_admin_0_countries_ind": "3e67a5a6ddeff3247ca8400cd2514fd4a5ac6e5432823b25d610a7028597d45f",
    "ne_10m_admin_1_states_provinces": "22d0e3ad85eb3e27f17cabf8ba2d50e554fbc27a87796ff891d958185da62fb5",
    "ne_10m_populated_places_simple": "fd3fa867a320cbd5c5b6bb5bc550afeec2939fb2cef688e508007282a55ac42f",
}
WORLD_BANK = "https://api.worldbank.org/v2/country/{countries}/indicator/{indicator}?format=json&date={start}:{end}&per_page=20000"
INDIA_CODE_SEARCH = "https://indiacode.gov.in/server/api/discover/search/objects"
INDIA_CODE_TERMS = ("Government of India content from India Code (Legislative Department, Ministry of Law and Justice); "
                    "Acts may be reproduced (Copyright Act 1957, s. 52(1)(q)) with the source acknowledged")
SC_JUDGMENTS = "https://indian-supreme-court-judgments.s3.amazonaws.com/metadata/parquet/year={year}/metadata.parquet"
SC_JUDGMENT_PDF = "https://indian-supreme-court-judgments.s3.amazonaws.com/data/pdf/year={year}/english/{path}_EN.pdf"
SC_CREDIT = ("Indian Supreme Court Judgments (Dattam Labs, Registry of Open Data on AWS), CC BY 4.0; "
             "judgments and metadata from the Supreme Court of India")
NOTO_DEVANAGARI = {"url": "https://raw.githubusercontent.com/google/fonts/e7db6ca603fd4862010383ff17ffd6cc4ffac1c0/ofl/"
                          "notosansdevanagari/NotoSansDevanagari%5Bwdth,wght%5D.ttf",
                   "sha256": "14ec4af41f27482216d1c2229f417ff9b1425e1babb014e57d1d40d03229853e",
                   "credit": "Noto Sans Devanagari, © The Noto Project Authors, SIL Open Font License 1.1"}
INDIC_NLP_RESOURCES = {   # anoopkunchukuttan/indic_nlp_resources at 5b4ff17c (MIT): the script tables the syllabifier reads
    "base": "https://raw.githubusercontent.com/anoopkunchukuttan/indic_nlp_resources/5b4ff17c080db4bc4cfc068deaa794aa87562eed/",
    "files": {"script/all_script_phonetic_data.csv": "4b0dd2d9c8cbc209b7466a979266a75a01572d5e5e8e6031bad18dacc2ef6c18",
              "script/tamil_script_phonetic_data.csv": "aacdc7c9ba87b1feeac6f104d4c14651f7239a8c48a90e71963a2156dc8e2f79"}}


class SourceError(ValueError):
    pass


def cache_dir() -> Path:
    path = Path(os.environ.get("BIE_ASSET_CACHE") or Path.home() / ".cache" / "bie" / "sources")
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch(url: str, *, opener=None, timeout: float = 300.0, max_bytes: int = MAX_BYTES, tries: int = 3) -> bytes:
    """GET an https URL; a busy or stumbling server's 429 or 5xx is asked again after a wait (F-15), like ``assets._open``."""
    if not url.startswith("https://"):
        raise SourceError("only https URLs are allowed")
    request = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    for attempt in range(tries):
        try:
            with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
                data = response.read(max_bytes + 1)
            break
        except urllib.error.HTTPError as exc:
            if exc.code not in TRANSIENT_HTTP or attempt == tries - 1:
                exc.msg = f"{exc.msg} ({url.split('?', 1)[0]}" + (f", {attempt + 1} tries)" if attempt else ")")
                raise
            wait = exc.headers.get("retry-after") if exc.headers else None
            time.sleep(min(30.0, float(wait) if wait and wait.isdigit() else 5.0 * (attempt + 1)))
    if len(data) > max_bytes:
        raise SourceError(f"{url}: larger than {max_bytes // (1024 * 1024)} MB")
    return data


def cached(url: str, name: str, *, opener=None) -> Path:
    """A big download kept once in the cache folder (outside git)."""
    path = cache_dir() / name
    if not path.exists() or path.stat().st_size == 0:
        data = fetch(url, opener=opener)
        tmp = path.with_suffix(path.suffix + ".part")
        tmp.write_bytes(data)
        tmp.replace(path)
    return path


def _check_licence(licence: str, where: str) -> list:
    """Refuse what the policy never fetches (non-commercial, no-derivatives); mark share-alike files."""
    if policy.never_fetched(licence):
        raise SourceError(f"{where}: licence {licence!r} cannot be used in a paid course")
    return ["share-alike"] if policy.normalise(licence) == "share-alike" else []


def rcsb_pdb(pdb_id: str, library: AssetLibrary, *, opener=None, tags=()):
    pdb_id = pdb_id.upper()
    if not re.fullmatch(r"[0-9][A-Z0-9]{3}", pdb_id):
        raise SourceError(f"{pdb_id!r} is not a PDB id")
    data = fetch(RCSB.format(id=pdb_id), opener=opener, max_bytes=50 * 1024 * 1024)
    return library.add_bytes(data, mime="chemical/x-pdb", source="rcsb_pdb", title=f"PDB {pdb_id}",
                             page_url=f"https://www.rcsb.org/structure/{pdb_id}", licence="CC0 1.0",
                             licence_url="https://creativecommons.org/publicdomain/zero/1.0/", author="wwPDB / RCSB PDB",
                             credit=f"RCSB PDB {pdb_id} (CC0)", tags=["protein", pdb_id.lower(), *tags])


def pubchem_sdf(name: str, library: AssetLibrary, *, opener=None, record: str = "3d", tags=()):
    url = PUBCHEM.format(name=urllib.parse.quote(name), record=record)
    data = fetch(url, opener=opener, max_bytes=10 * 1024 * 1024)
    if b"$$$$" not in data:
        raise SourceError(f"PubChem has no {record} record for {name!r}")
    return library.add_bytes(data, mime="chemical/x-mdl-sdfile", source="pubchem", title=f"PubChem {name} ({record})",
                             page_url=f"https://pubchem.ncbi.nlm.nih.gov/compound/{urllib.parse.quote(name)}",
                             licence="Public domain (NCBI PubChem)", licence_url="https://www.ncbi.nlm.nih.gov/home/about/policies/",
                             author="NCBI PubChem", credit=f"PubChem: {name}", tags=["molecule", name.lower(), *tags])


def nih3d(entry_id: str, library: AssetLibrary, *, opener=None, formats=("GLB", "STL"), tags=()):
    """The newest published file of an NIH 3D entry in the first available format, with the entry's own licence."""
    meta = json.loads(fetch(NIH_ENTRY.format(id=urllib.parse.quote(entry_id)), opener=opener, max_bytes=8 * 1024 * 1024))
    published = [s for s in meta.get("submissions") or [] if s.get("submissionStatus") == "Published"]
    if not published:
        raise SourceError(f"NIH 3D {entry_id}: no published submission")
    sub = max(published, key=lambda s: float(s.get("version") or 0))
    files = list(sub.get("inputFiles") or []) + [f for run in sub.get("workflowRuns") or [] for f in run.get("outputFiles") or []]
    pick = next((f for fmt in formats for f in files if str(f.get("fileFormat", "")).upper() == fmt), None)
    if pick is None:
        raise SourceError(f"NIH 3D {entry_id}: no file in {', '.join(formats)}")
    md = sub.get("metadata") or {}
    licence = str(md.get("license") or "unknown")
    extra = _check_licence(licence, f"NIH 3D {entry_id}")
    data = fetch(NIH_DOWNLOAD.format(submission=sub["submissionId"], file=pick["fileId"]), opener=opener, max_bytes=120 * 1024 * 1024)
    mime = "model/gltf-binary" if pick["fileFormat"].upper() == "GLB" else "model/stl"
    if mime == "model/gltf-binary" and data[:4] != b"glTF":
        raise SourceError(f"NIH 3D {entry_id}: the download is not a glTF binary")
    title = md.get("title") or entry_id
    return library.add_bytes(data, mime=mime, source="nih_3d", title=f"{title} (NIH 3D {meta.get('threedpxId', entry_id)})",
                             page_url=f"https://3d.nih.gov/entries/{meta.get('threedpxId', entry_id)}", licence=licence,
                             licence_url="", author=str(md.get("author") or meta.get("createdBy") or "NIH 3D contributor"),
                             credit=f"NIH 3D {meta.get('threedpxId', entry_id)} · {licence}", tags=["model", *extra, *tags])


def servier(path: str, library: AssetLibrary, *, opener=None, title: str = "", tags=()):
    """A Servier Medical Art picture by its upload path (for example '2016/10/poumon_10.png')."""
    if not re.fullmatch(r"\d{4}/\d{2}/[A-Za-z0-9_.-]+\.(png|jpg)", path):
        raise SourceError(f"{path!r} is not a Servier upload path")
    data = fetch(SERVIER_FILE.format(path=path), opener=opener, max_bytes=20 * 1024 * 1024)
    mime = "image/png" if path.endswith(".png") else "image/jpeg"
    return library.add_bytes(data, mime=mime, source="servier_medical_art", title=title or path.rsplit("/", 1)[-1],
                             page_url="https://smart.servier.com", licence="CC BY 4.0",
                             licence_url="https://creativecommons.org/licenses/by/4.0/", author="Servier Medical Art",
                             credit="Servier Medical Art (smart.servier.com), CC BY 4.0", tags=["illustration", *tags])


def bodyparts3d(concept: str, library: AssetLibrary, *, opener=None, name: str = "", tags=(), max_parts: int = 200):
    """One BodyParts3D concept (an FMA id such as FMA7088, the heart) from its element meshes, as a single .glb."""
    from .adapters.base import need
    trimesh = need("trimesh")
    if not re.fullmatch(r"FMA\d+", concept):
        raise SourceError(f"{concept!r} is not an FMA id")
    table = cached(BP3D_ELEMENTS, "bp3d_partof_element_parts.txt", opener=opener).read_text(encoding="utf-8", errors="replace")
    rows = [line.split("\t") for line in table.splitlines()[1:] if line.startswith(concept + "\t")]
    if not rows:
        raise SourceError(f"BodyParts3D has no concept {concept}")
    label = name or rows[0][1]
    elements = [r[2].strip() for r in rows][:max_parts]
    archive = zipfile.ZipFile(cached(BP3D_ZIP, "partof_BP3D_4.0_obj_99.zip", opener=opener))
    members = {Path(n).stem: n for n in archive.namelist() if n.endswith(".obj")}
    scene = trimesh.Scene()
    for element in elements:
        if element in members:
            mesh = trimesh.load(io.BytesIO(archive.read(members[element])), file_type="obj", force="mesh")
            mesh.visual = trimesh.visual.ColorVisuals(mesh, face_colors=(205, 92, 92, 255))
            scene.add_geometry(mesh, node_name=element)
    if not scene.geometry:
        raise SourceError(f"BodyParts3D {concept}: none of its element files are in the archive")
    glb = trimesh.exchange.gltf.export_glb(scene)
    return library.add_bytes(glb, mime="model/gltf-binary", source="bodyparts3d", title=f"{label} (BodyParts3D {concept})",
                             page_url="https://dbarchive.biosciencedbc.jp/en/bodyparts3d/", licence="CC BY 4.0",
                             licence_url="https://creativecommons.org/licenses/by/4.0/", author="Database Center for Life Science",
                             credit=BP3D_CREDIT, tags=["anatomy", concept.lower(), *tags])


def z_anatomy(system: str, match: str, library: AssetLibrary, *, opener=None, exclude: str = "", title: str = "", tags=(),
              group: str = "", min_vertices: int = 0):
    """Parts of a Z-Anatomy body system (an FBX such as 'CardioVascular41') exported by Blender as one .glb; ``group``
    joins the parts into one object per matching parent (``NervousSystem100`` with lobe groups gives a brain by lobes)."""
    from .adapters import blender
    if not re.fullmatch(r"[A-Za-z0-9 ]{3,60}", system):
        raise SourceError(f"{system!r} is not a Z-Anatomy system file name")
    fbx = cached(ZANATOMY_FBX.format(name=urllib.parse.quote(system)), f"z-anatomy-{system.replace(' ', '_')}.fbx", opener=opener)
    spec = [system, match, exclude] + ([group, min_vertices] if group or min_vertices else [])
    key = hashlib.sha256(json.dumps(spec).encode()).hexdigest()[:16]   # same parts, same file, every run
    out = cache_dir() / f"z-anatomy-{key}.glb"
    info = blender.fbx_part(fbx, match, out, exclude=exclude, group=group, min_vertices=min_vertices)
    asset = library.add_bytes(out.read_bytes(), mime="model/gltf-binary", source="z_anatomy", title=title or f"{system}: {match}",
                              page_url="https://github.com/LluisV/Z-Anatomy", licence="CC BY-SA 4.0",
                              licence_url="https://creativecommons.org/licenses/by-sa/4.0/", author="Z-Anatomy project (github.com/LluisV)",
                              credit="Z-Anatomy, CC BY-SA 4.0", tags=["anatomy", "share-alike", *tags],
                              description=", ".join(info.get("names", [])[:20]))
    return asset, info


def usgs_quakes(start: str, end: str, library: AssetLibrary, *, magnitude: float = 6.5, opener=None, tags=()):
    """Earthquakes from the USGS catalogue (public domain) as a GeoJSON asset, and the rows a map block needs."""
    for day in (start, end):
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", day):
            raise SourceError(f"{day!r} is not a date (YYYY-MM-DD)")
    data = fetch(USGS_QUAKES.format(start=start, end=end, magnitude=magnitude), opener=opener, max_bytes=40 * 1024 * 1024)
    collection = json.loads(data)
    rows = [{"lon": f["geometry"]["coordinates"][0], "lat": f["geometry"]["coordinates"][1], "depth_km": f["geometry"]["coordinates"][2],
             "magnitude": f["properties"]["mag"], "time_ms": f["properties"]["time"], "place": f["properties"].get("place") or ""}
            for f in collection.get("features") or []]
    asset = library.add_bytes(data, mime="application/json", source="usgs_earthquakes",
                              title=f"USGS earthquakes M{magnitude}+ {start} to {end}", page_url="https://earthquake.usgs.gov/earthquakes/search/",
                              licence="Public domain (USGS)", licence_url="https://www.usgs.gov/information-policies-and-instructions/copyrights-and-credits",
                              author="U.S. Geological Survey", credit="Earthquake data: U.S. Geological Survey", tags=["earthquakes", *tags])
    return asset, rows


def gplates_model(model: str = "muller2019", *, opener=None) -> dict:
    """A published plate model's rotation file and coastlines, unpacked once into the cache (outside git)."""
    if model not in GPLATES_MODELS:
        raise SourceError(f"unknown plate model {model!r}")
    spec = GPLATES_MODELS[model]
    out = {"credit": spec["credit"], "licence": spec["licence"]}
    for key in ("rotations", "coastlines"):
        archive_name, member = spec[key]
        target = cache_dir() / f"gplates-{model}" / member
        if not target.exists():
            archive = zipfile.ZipFile(cached(spec["base"] + archive_name, f"gplates-{model}-{archive_name}", opener=opener))
            if member not in archive.namelist():
                raise SourceError(f"{archive_name} has no {member}")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(archive.read(member))          # one named member only: nothing else from the archive is written
        out[key] = target
    return out


def nasa_image(nasa_id: str, library: AssetLibrary, *, size: str = "large", opener=None, tags=()):
    """A picture from NASA's Image and Video Library with its title and centre. NASA media are US government works,
    public domain (NASA Images and Media Usage Guidelines) unless the record names a third-party copyright holder; the
    licence is recorded per item from its metadata, and the licence policy refuses a third-party file for lessons."""
    if not re.fullmatch(r"[A-Za-z0-9_.-]{3,80}", nasa_id):
        raise SourceError(f"{nasa_id!r} is not a NASA image id")
    found = json.loads(fetch(NASA_SEARCH.format(id=nasa_id), opener=opener, max_bytes=4 * 1024 * 1024))
    items = found.get("collection", {}).get("items") or []
    if not items:
        raise SourceError(f"NASA image {nasa_id} not found")
    meta = items[0]["data"][0]
    files = [i["href"] for i in json.loads(fetch(NASA_ASSET.format(id=nasa_id), opener=opener, max_bytes=4 * 1024 * 1024))
             .get("collection", {}).get("items") or []]
    pick = next((f for f in files if f.endswith(f"~{size}.jpg")), None) or next((f for f in files if f.endswith(".jpg")), None)
    if pick is None:
        raise SourceError(f"NASA image {nasa_id}: no JPEG")
    data = fetch(pick.replace("http://", "https://", 1), opener=opener, max_bytes=40 * 1024 * 1024)
    holder = " ".join(str(meta.get(k) or "") for k in ("secondary_creator", "photographer")).strip()
    licence = "Public domain (NASA, US government work; NASA Images and Media Usage Guidelines)"
    if "©" in holder or "copyright" in holder.lower():
        licence = f"third-party copyright ({holder}): check before use"
    return library.add_bytes(data, mime="image/jpeg", source="nasa_images", title=meta.get("title") or nasa_id,
                             page_url=f"https://images.nasa.gov/details/{nasa_id}", licence=licence,
                             licence_url="https://www.nasa.gov/nasa-brand-center/images-and-media/",
                             author=f"NASA {meta.get('center') or ''}".strip(), credit=f"NASA/{meta.get('center') or 'NASA'} ({nasa_id})",
                             tags=["nasa", *tags], description=(meta.get("description") or "")[:400])


# ---------------------------------------------------------------- batch 3


def _pinned(url: str, name: str, sha256: str, *, opener=None) -> Path:
    """A cached download whose content hash must match the pinned one (the same file on every machine, every run)."""
    path = cached(url, name, opener=opener)
    found = hashlib.sha256(path.read_bytes()).hexdigest()
    if found != sha256:
        path.unlink()
        raise SourceError(f"{name}: content hash {found[:12]} is not the pinned {sha256[:12]}")
    return path


def natural_earth(name: str, *, opener=None) -> Path:
    """One Natural Earth 5.1.2 GeoJSON file (public domain), cached outside git and checked against its pinned hash."""
    if name not in NATURAL_EARTH_FILES:
        raise SourceError(f"{name!r} is not a pinned Natural Earth file")
    return _pinned(NATURAL_EARTH.format(name=name), f"natural-earth-5.1.2-{name}.geojson", NATURAL_EARTH_FILES[name], opener=opener)


def world_bank(indicator: str, countries, start: int, end: int, library: AssetLibrary, *, opener=None, tags=()):
    """Values of one World Bank indicator (World Development Indicators, CC BY 4.0) for countries and years, as an asset
    and as rows {country, iso3, year, value} (years without a value are left out)."""
    if not re.fullmatch(r"[A-Z]{2,3}(\.[A-Z0-9]{2,8}){1,5}", indicator):
        raise SourceError(f"{indicator!r} is not a World Bank indicator code")
    codes = [c.upper() for c in countries]
    if not codes or not all(re.fullmatch(r"[A-Z0-9]{2,3}", c) for c in codes):
        raise SourceError("countries must be ISO codes")
    data = fetch(WORLD_BANK.format(countries=";".join(codes), indicator=indicator, start=int(start), end=int(end)), opener=opener,
                 max_bytes=20 * 1024 * 1024)
    body = json.loads(data)
    if not isinstance(body, list) or len(body) < 2 or body[1] is None:
        raise SourceError(f"World Bank: no data for {indicator} ({str(body)[:200]})")
    rows = [{"country": r["country"]["value"], "iso3": r.get("countryiso3code") or r["country"]["id"], "year": int(r["date"]),
             "value": r["value"]} for r in body[1] if r.get("value") is not None]
    name = body[1][0]["indicator"]["value"] if body[1] else indicator
    asset = library.add_bytes(data, mime="application/json", source="world_bank", title=f"World Bank {indicator}: {name}",
                              page_url=f"https://data.worldbank.org/indicator/{indicator}", licence="CC BY 4.0",
                              licence_url="https://datacatalog.worldbank.org/public-licenses#cc-by", author="The World Bank",
                              credit=f"World Bank, World Development Indicators ({indicator}), CC BY 4.0", tags=["data", indicator.lower(), *tags])
    return asset, sorted(rows, key=lambda r: (r["iso3"], r["year"])), {"indicator": indicator, "name": name}


def _india_code(query: str, *, page: int = 0, size: int = 100, sort: str = "", opener=None) -> dict:
    params = {"query": query, "dsoType": "ITEM", "size": str(size), "page": str(page)}
    if sort:
        params["sort"] = sort
    body = json.loads(fetch(INDIA_CODE_SEARCH + "?" + urllib.parse.urlencode(params), opener=opener, timeout=120, max_bytes=20 * 1024 * 1024))
    return body["_embedded"]["searchResult"]


def _meta(item: dict, key: str, default: str = "") -> str:
    values = item.get("metadata", {}).get(key) or []
    return str(values[0].get("value")) if values else default


def india_code_act(act_id: str, library: AssetLibrary, *, opener=None, tags=()):
    """A central Act from India Code (the official repository of Indian law) as data: the Act's record and every section
    (number, official title, text), read through India Code's open REST API (DSpace) and kept in the cache.

    ``act_id`` is India Code's own id (dc.identifier.act_id), for example the Bharatiya Nagarik Suraksha Sanhita, 2023:
    AC_CEN_5_23_00049_202346_1719552320687."""
    if not re.fullmatch(r"AC_[A-Z]{2,4}_[0-9_]{6,60}", act_id):
        raise SourceError(f"{act_id!r} is not an India Code act id")
    store = cache_dir() / f"india-code-{act_id}.json"
    if store.exists():
        act = json.loads(store.read_text(encoding="utf-8"))
    else:
        found = _india_code(f"dc.identifier.act_id:{act_id} AND dc.identifier.collection:ACT", size=5, opener=opener)
        items = [o["_embedded"]["indexableObject"] for o in found["_embedded"]["objects"]]
        if not items:
            raise SourceError(f"India Code has no act {act_id}")
        item = items[0]
        act = {"act_id": act_id, "title": item.get("name", ""), "act_number": _meta(item, "dc.identifier.act_number"),
               "year": _meta(item, "dc.date.act_year"), "enacted": _meta(item, "dc.date.enact_date"),
               "in_force": _meta(item, "dc.date.enforcement_date"), "long_title": _meta(item, "dc.title.long_title"),
               "ministry": _meta(item, "dc.identifier.ministry_name"), "handle": item.get("handle", ""), "sections": []}
        page, pages = 0, 1
        while page < pages:                       # sorted by title: India Code's paging is only stable with a sort
            found = _india_code(f"dc.identifier.act_id:{act_id} AND dc.identifier.collection:SECTION", page=page,
                                sort="dc.title,ASC", opener=opener)
            pages = int(found["page"]["totalPages"])
            for o in found["_embedded"]["objects"]:
                sec = o["_embedded"]["indexableObject"]
                text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", _meta(sec, "dc.identifier.section_page_note"))).strip()
                act["sections"].append({"number": _meta(sec, "dc.identifier.section_number"), "title": sec.get("name", "").strip(),
                                        "text": text})
            page += 1
        numbers = [s["number"] for s in act["sections"]]
        if len(set(numbers)) != len(numbers):
            raise SourceError(f"India Code act {act_id}: sections repeat across pages")
        act["sections"].sort(key=lambda s: (int(re.match(r"\d+", s["number"]).group()) if re.match(r"\d+", s["number"]) else 0, s["number"]))
        store.write_text(json.dumps(act, ensure_ascii=False), encoding="utf-8")
    data = json.dumps(act, ensure_ascii=False).encode("utf-8")
    asset = library.add_bytes(data, mime="application/json", source="india_code", title=f"{act['title']} (India Code)",
                              page_url=f"https://indiacode.gov.in/handle/{act['handle']}", licence=INDIA_CODE_TERMS,
                              licence_url="https://indiacode.gov.in", author="Legislative Department, Government of India",
                              credit=f"India Code: {act['title']}", tags=["law", "bare-act", *tags])
    return asset, act


def sc_judgment(year: int, match: str, library: AssetLibrary, *, opener=None, tags=()):
    """One Supreme Court of India judgment's record (title, parties, bench, citations, date) from the year's metadata
    in the open Indian Supreme Court Judgments dataset (CC BY 4.0), found by a regular expression on the title."""
    from .adapters.base import need
    need("pyarrow")
    import pyarrow.parquet as pq
    if not 1950 <= int(year) <= 2100:
        raise SourceError(f"{year} is not a Supreme Court year")
    table = pq.read_table(cached(SC_JUDGMENTS.format(year=int(year)), f"sc-judgments-{int(year)}.parquet", opener=opener)).to_pylist()
    pattern = re.compile(match, re.I)
    rows = [r for r in table if pattern.search(str(r.get("title") or ""))]
    if len(rows) != 1:
        raise SourceError(f"{len(rows)} judgments of {year} match {match!r}; name exactly one")
    row = rows[0]
    raw = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " | ", str(row.get("raw_html") or "")))
    bench = re.search(r"Bench\s*:\s*\|[\s|]*(\d+)\s*Judges", raw)
    coram = re.search(r"Coram\s*:\s*(.*?)\s*\|\s*\|", raw)
    record = {k: (None if row.get(k) in ("", "<NA>") else row.get(k)) for k in
              ("title", "petitioner", "respondent", "judge", "author_judge", "citation", "case_id", "cnr", "decision_date",
               "disposal_nature", "court", "available_languages", "path", "year")}
    record["bench_judges"] = int(bench.group(1)) if bench else None
    record["coram"] = [c.strip(" *,") for c in re.split(r"\s*,\s*|\s*\|\s*\*\s*\|\s*", coram.group(1)) if c.strip(" *,|")] if coram else []
    record["pdf"] = SC_JUDGMENT_PDF.format(year=int(year), path=row.get("path"))
    data = json.dumps(record, ensure_ascii=False).encode("utf-8")
    asset = library.add_bytes(data, mime="application/json", source="sc_judgments", title=f"{record['title']} ({record['case_id']})",
                              page_url="https://registry.opendata.aws/indian-supreme-court-judgments/", licence="CC BY 4.0",
                              licence_url="https://creativecommons.org/licenses/by/4.0/", author="Supreme Court of India; dataset by Dattam Labs",
                              credit=SC_CREDIT, tags=["law", "judgment", *tags])
    return asset, record


def noto_devanagari(library: AssetLibrary, *, opener=None):
    """Noto Sans Devanagari (variable font, SIL OFL 1.1) for Devanagari and Roman text in the video."""
    path = _pinned(NOTO_DEVANAGARI["url"], "NotoSansDevanagari-variable.ttf", NOTO_DEVANAGARI["sha256"], opener=opener)
    return library.add_bytes(path.read_bytes(), mime="font/ttf", source="google_fonts", title="Noto Sans Devanagari",
                             page_url="https://fonts.google.com/noto/specimen/Noto+Sans+Devanagari", licence="SIL Open Font License 1.1",
                             licence_url="https://openfontlicense.org", author="The Noto Project Authors", credit=NOTO_DEVANAGARI["credit"],
                             tags=["font", "devanagari"])


def indic_nlp_resources(*, opener=None) -> Path:
    """The folder of Indic NLP resources the syllabifier needs (only the script tables, pinned by hash)."""
    root = cache_dir() / "indic_nlp_resources"
    for rel, sha in INDIC_NLP_RESOURCES["files"].items():
        target = root / rel
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(_pinned(INDIC_NLP_RESOURCES["base"] + rel, "indic-nlp-" + rel.replace("/", "-"), sha, opener=opener).read_bytes())
    return root


def _open_image(kind: str, key: str, find, library: AssetLibrary, *, opener=None, tags=()):
    """A picture from an open archive, its record and bytes kept in the cache after the first fetch (archives such as
    Commons slow down busy clients; a run should not need them twice), then added to the library with its licence."""
    stem = cache_dir() / "open-images" / f"{kind}-{hashlib.sha256(key.encode()).hexdigest()[:16]}"
    record, blob = stem.with_suffix(".json"), stem.with_suffix(".bin")
    if record.exists() and blob.exists():
        candidate, data = Candidate(**json.loads(record.read_text(encoding="utf-8"))), blob.read_bytes()
    else:
        candidate = find()
        _check_licence(candidate.licence, key)
        verdict = policy.asset_verdict(candidate)          # a per-item source: this file must be fit for a lesson
        if not verdict.allowed:
            raise SourceError(f"{key}: {verdict.text} for lessons: {verdict.reason}")
        data = open_url(candidate.file_url, opener=opener)
        stem.parent.mkdir(parents=True, exist_ok=True)
        blob.write_bytes(data)
        record.write_text(json.dumps(candidate.__dict__, ensure_ascii=False), encoding="utf-8")
    return library.add_candidate(candidate, tags=[kind, *tags], data=data)


def commons_image(title: str, library: AssetLibrary, *, opener=None, tags=(), width: int = 1280):
    """A named Wikimedia Commons picture through the asset library, only when a lesson may use it (licence policy)."""
    return _open_image("commons", f"{title}@{width}", lambda: commons_file(title, thumb_width=width, opener=opener), library,
                       opener=opener, tags=tags)


def openverse_image(identifier: str, library: AssetLibrary, *, opener=None, tags=()):
    """An Openverse picture by id through the asset library, only when a lesson may use it (licence policy)."""
    return _open_image("openverse", identifier, lambda: openverse_candidate(identifier, opener=opener), library, opener=opener, tags=tags)
