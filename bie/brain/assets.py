"""Open asset search and BIE's asset library, with licences kept for every file.

The visual section asks for an asset by description; BIE searches open sources (first: Wikimedia
Commons), keeps only licences that allow use in a paid course, downloads the chosen file into the
asset library with its source, author and licence, and produces credits for every video. Files
under share-alike licences (CC BY-SA) are kept out unless ``allow_share_alike`` is set, because a
video that adapts them may have to carry the same licence; that is Navin's decision.

Network access runs in GitHub Actions; tests use a fake opener.
"""
from __future__ import annotations

import hashlib
import json
import re
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
USER_AGENT = "BIE-asset-search/1.0 (https://github.com/SEENAV01/Enterprise-bie)"
MAX_ASSET_BYTES = 25 * 1024 * 1024
IMAGE_TYPES = ("image/png", "image/jpeg", "image/svg+xml", "image/webp")
# File suffix per media type; the 3D, structure and data types come with the toolbox sources (Task 046a).
SUFFIXES = {"image/png": ".png", "image/jpeg": ".jpg", "image/svg+xml": ".svg", "image/webp": ".webp",
            "model/gltf-binary": ".glb", "model/stl": ".stl", "model/obj": ".obj", "chemical/x-pdb": ".pdb",
            "chemical/x-mdl-sdfile": ".sdf", "application/json": ".json", "text/csv": ".csv"}


class AssetError(ValueError):
    pass


@dataclass(frozen=True)
class Candidate:
    source: str
    title: str
    page_url: str
    file_url: str
    thumb_url: str
    width: int
    height: int
    mime: str
    licence: str
    licence_url: str
    author: str
    credit: str


@dataclass
class Asset:
    asset_id: str
    path: str
    sha256: str
    mime: str
    source: str
    title: str
    page_url: str
    licence: str
    licence_url: str
    author: str
    credit: str
    tags: list = field(default_factory=list)
    description: str = ""


def normalise_licence(name: str) -> str:
    text = re.sub(r"\s+", " ", (name or "").strip().lower())
    if not text:
        return "unknown"
    if "cc0" in text or "public domain" in text or text in ("pd", "pdm"):
        return "public-domain"
    if text.startswith("cc by-sa") or text.startswith("cc-by-sa"):
        return "cc-by-sa"
    if text.startswith("cc by-nc") or "noncommercial" in text or "-nc" in text:
        return "non-commercial"
    if text.startswith("cc by-nd") or "-nd" in text:
        return "no-derivatives"
    if text.startswith("cc by") or text.startswith("cc-by"):
        return "cc-by"
    if "gfdl" in text:
        return "gfdl"
    return "other"


def licence_allowed(licence: str, *, allow_share_alike: bool = False) -> bool:
    kind = normalise_licence(licence)
    return kind in ("public-domain", "cc-by") or (allow_share_alike and kind == "cc-by-sa")


def _strip_html(text) -> str:
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


def _open(url: str, *, opener=None, timeout: float = 60.0, max_bytes: int = MAX_ASSET_BYTES) -> bytes:
    if not url.startswith("https://"):
        raise AssetError("only https URLs are allowed")
    request = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
        data = response.read(max_bytes + 1)
    if len(data) > max_bytes:
        raise AssetError("asset is larger than the limit")
    return data


def search_commons(query: str, *, limit: int = 12, thumb_width: int = 800, allow_share_alike: bool = False, opener=None):
    """Image candidates from Wikimedia Commons whose licence allows use in a paid course."""
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6", "gsrlimit": str(limit),
              "gsrsearch": f"{query} filetype:bitmap|drawing", "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(thumb_width)}
    raw = _open(COMMONS_API + "?" + urllib.parse.urlencode(params), opener=opener, max_bytes=8 * 1024 * 1024)
    pages = (json.loads(raw.decode("utf-8")).get("query") or {}).get("pages") or {}
    found = []
    for page in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        licence = _strip_html((meta.get("LicenseShortName") or {}).get("value"))
        if info.get("mime") not in IMAGE_TYPES or not licence_allowed(licence, allow_share_alike=allow_share_alike):
            continue
        found.append(Candidate(
            source="wikimedia_commons", title=page.get("title", ""), page_url=info.get("descriptionurl", ""),
            file_url=info.get("url", ""), thumb_url=info.get("thumburl") or info.get("url", ""),
            width=int(info.get("width") or 0), height=int(info.get("height") or 0), mime=info.get("mime", ""),
            licence=licence, licence_url=_strip_html((meta.get("LicenseUrl") or {}).get("value")),
            author=_strip_html((meta.get("Artist") or {}).get("value"))[:300],
            credit=_strip_html((meta.get("Credit") or {}).get("value"))[:300]))
    return found


class AssetLibrary:
    """A folder of licensed assets with an index; the same file is stored once (by content hash)."""

    def __init__(self, folder: str | Path):
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.index_path = self.folder / "index.json"
        self.assets = {}
        if self.index_path.exists():
            for row in json.loads(self.index_path.read_text(encoding="utf-8")).get("assets", []):
                self.assets[row["asset_id"]] = Asset(**row)

    def save(self):
        rows = [asdict(a) for a in sorted(self.assets.values(), key=lambda a: a.asset_id)]
        self.index_path.write_text(json.dumps({"schema": "bie.brain.asset-library/1", "assets": rows}, ensure_ascii=False,
                                              indent=1), encoding="utf-8")

    def add_candidate(self, candidate: Candidate, *, tags=(), description: str = "", opener=None,
                      allow_share_alike: bool = False) -> Asset:
        if not licence_allowed(candidate.licence, allow_share_alike=allow_share_alike):
            raise AssetError(f"licence {candidate.licence!r} is not allowed")
        data = _open(candidate.file_url, opener=opener)
        return self.add_bytes(data, mime=candidate.mime, source=candidate.source, title=candidate.title,
                              page_url=candidate.page_url, licence=candidate.licence, licence_url=candidate.licence_url,
                              author=candidate.author, credit=candidate.credit, tags=tags, description=description)

    def add_bytes(self, data: bytes, *, mime: str, source: str, title: str, page_url: str, licence: str, licence_url: str,
                  author: str, credit: str, tags=(), description: str = "") -> Asset:
        digest = hashlib.sha256(data).hexdigest()
        asset_id = "a-" + digest[:16]
        if asset_id in self.assets:
            asset = self.assets[asset_id]
            asset.tags = sorted(set(asset.tags) | set(tags))
            self.save()
            return asset
        suffix = SUFFIXES.get(mime, ".bin")
        path = self.folder / "files" / (asset_id + suffix)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        asset = Asset(asset_id=asset_id, path=str(path.relative_to(self.folder)), sha256=digest, mime=mime, source=source,
                      title=title, page_url=page_url, licence=licence, licence_url=licence_url, author=author, credit=credit,
                      tags=sorted(set(tags)), description=description)
        self.assets[asset_id] = asset
        self.save()
        return asset

    def find(self, tags) -> list:
        wanted = {t.lower() for t in tags}
        scored = [(len(wanted & {t.lower() for t in a.tags}), a) for a in self.assets.values()]
        return [a for score, a in sorted(scored, key=lambda x: (-x[0], x[1].asset_id)) if score]

    def credits(self, asset_ids) -> list:
        lines = []
        for asset_id in asset_ids:
            a = self.assets.get(asset_id)
            if a and a.source != "bie":
                lines.append(f"{a.title} · {a.author or 'unknown author'} · {a.licence} · {a.page_url}")
        return lines
