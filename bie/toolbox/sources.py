"""Asset sources of the toolbox (Task 046a): models, structures and pictures fetched on demand into BIE's asset
library (``bie.brain.assets.AssetLibrary``) with their licence, source page and credit. Nothing large goes into git:
big downloads (zip archives, FBX files) stay in a cache folder outside the repository (``BIE_ASSET_CACHE``, default
``~/.cache/bie/sources``) and only the file a video needs (a .glb, a .pdb, a .png) enters the library.

Licences are recorded as each source states them; share-alike files (Z-Anatomy) are kept and tagged "share-alike"
for Navin's licence decision; non-commercial and no-derivatives files are refused, because a paid course cannot use
them at all. Every fetch takes an ``opener`` so tests run offline.
"""
from __future__ import annotations

import hashlib
import io
import json
import os
import re
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

from bie.brain.assets import USER_AGENT, AssetLibrary, normalise_licence

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
REFUSED = ("non-commercial", "no-derivatives")


class SourceError(ValueError):
    pass


def cache_dir() -> Path:
    path = Path(os.environ.get("BIE_ASSET_CACHE") or Path.home() / ".cache" / "bie" / "sources")
    path.mkdir(parents=True, exist_ok=True)
    return path


def fetch(url: str, *, opener=None, timeout: float = 300.0, max_bytes: int = MAX_BYTES) -> bytes:
    if not url.startswith("https://"):
        raise SourceError("only https URLs are allowed")
    request = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
        data = response.read(max_bytes + 1)
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
    kind = normalise_licence(licence)
    if kind in REFUSED:
        raise SourceError(f"{where}: licence {licence!r} cannot be used in a paid course")
    return ["share-alike"] if kind == "cc-by-sa" else []


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


def z_anatomy(system: str, match: str, library: AssetLibrary, *, opener=None, exclude: str = "", title: str = "", tags=()):
    """Parts of a Z-Anatomy body system (an FBX such as 'CardioVascular41') exported by Blender as one .glb."""
    from .adapters import blender
    if not re.fullmatch(r"[A-Za-z0-9 ]{3,60}", system):
        raise SourceError(f"{system!r} is not a Z-Anatomy system file name")
    fbx = cached(ZANATOMY_FBX.format(name=urllib.parse.quote(system)), f"z-anatomy-{system.replace(' ', '_')}.fbx", opener=opener)
    key = hashlib.sha256(json.dumps([system, match, exclude]).encode()).hexdigest()[:16]   # same parts, same file, every run
    out = cache_dir() / f"z-anatomy-{key}.glb"
    info = blender.fbx_part(fbx, match, out, exclude=exclude)
    asset = library.add_bytes(out.read_bytes(), mime="model/gltf-binary", source="z_anatomy", title=title or f"{system}: {match}",
                              page_url="https://github.com/LluisV/Z-Anatomy", licence="CC BY-SA 4.0",
                              licence_url="https://creativecommons.org/licenses/by-sa/4.0/", author="Z-Anatomy project (github.com/LluisV)",
                              credit="Z-Anatomy, CC BY-SA 4.0", tags=["anatomy", "share-alike", *tags],
                              description=", ".join(info.get("names", [])[:20]))
    return asset, info
