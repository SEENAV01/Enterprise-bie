"""Open asset search and BIE's asset library, with licences kept for every file.

The visual section asks for an asset by description; BIE searches open sources (first: Wikimedia
Commons), keeps only files whose licence the licence policy allows in a lesson, downloads the chosen
file into the asset library with its source, author and licence, and produces credits for every video.
Every licence decision reads ``bie/toolbox/licence_policy.json`` through ``bie.toolbox.licence``
(Navin, 25 October 2026: "Final videos mein sirf CC0 aur CC BY assets lein; CC BY-SA nahi; NC bilkul
nahi."). There is no switch that lets share-alike files into a lesson.

Network access runs in GitHub Actions; tests use a fake opener.
"""
from __future__ import annotations

import errno
import hashlib
import json
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass, field
from pathlib import Path

from bie.toolbox import licence as policy

COMMONS_API = "https://commons.wikimedia.org/w/api.php"
OPENVERSE_API = "https://api.openverse.org/v1/images/"
# Openverse licence codes → the names normalise_licence() reads (Task 046a, batch 3)
OPENVERSE_LICENCES = {"by": "CC BY", "by-sa": "CC BY-SA", "cc0": "CC0", "pdm": "Public Domain Mark", "by-nc": "CC BY-NC",
                      "by-nd": "CC BY-ND", "by-nc-sa": "CC BY-NC-SA", "by-nc-nd": "CC BY-NC-ND", "sampling+": "CC Sampling+",
                      "nc-sampling+": "CC NC-Sampling+"}
USER_AGENT = "BIE-asset-search/1.0 (https://github.com/SEENAV01/Enterprise-bie)"
MAX_ASSET_BYTES = 25 * 1024 * 1024
IMAGE_TYPES = ("image/png", "image/jpeg", "image/svg+xml", "image/webp")
# File suffix per media type; the 3D, structure and data types come with the toolbox sources (Task 046a).
SUFFIXES = {"image/png": ".png", "image/jpeg": ".jpg", "image/svg+xml": ".svg", "image/webp": ".webp",
            "model/gltf-binary": ".glb", "model/stl": ".stl", "model/obj": ".obj", "chemical/x-pdb": ".pdb",
            "chemical/x-mdl-sdfile": ".sdf", "application/json": ".json", "text/csv": ".csv", "font/ttf": ".ttf"}


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
    """The licence policy's class of a licence: public-domain, cc-by, share-alike, non-commercial, no-derivatives, ..."""
    return policy.normalise(name)


def licence_allowed(licence: str) -> bool:
    """True when the licence policy allows this licence in a lesson (CC0, public domain, CC BY)."""
    return policy.allowed(licence)


def lesson_ready(candidate) -> bool:
    """A search result a lesson may use: its licence and source are allowed and a CC BY file names its author, licence,
    licence URL and page (``bie.toolbox.licence.asset_verdict``)."""
    return policy.asset_verdict(candidate).allowed


def _strip_html(text) -> str:
    return re.sub(r"<[^>]+>", "", str(text or "")).strip()


TRANSIENT_HTTP = (429, 500, 502, 503, 504)   # a busy or stumbling server: asked again after a wait, never on a 4xx of our own making
TRANSIENT_ERRNO = (errno.ECONNRESET, errno.ETIMEDOUT, errno.ECONNREFUSED, errno.EPIPE)   # the line dropped mid-way: asked again too


def transient(exc: BaseException) -> bool:
    """Whether an error is the server's or the line's passing trouble (asked again after a wait) rather than ours: a 429 or
    5xx, a socket read that timed out, a connection reset or refused (F-15, 27 October 2026; F-17, 29 October 2026: Commons
    or Openverse let a read time out once and the archive demo failed). A 4xx of our own making is never transient."""
    if isinstance(exc, urllib.error.HTTPError):
        return exc.code in TRANSIENT_HTTP
    if isinstance(exc, (TimeoutError, socket.timeout)):
        return True
    if isinstance(exc, urllib.error.URLError):
        return transient(exc.reason) if isinstance(exc.reason, BaseException) else "timed out" in str(exc.reason).lower()
    if isinstance(exc, OSError):
        return exc.errno in TRANSIENT_ERRNO or "timed out" in str(exc).lower()
    return False


def transient_wait(exc: BaseException, attempt: int) -> float:
    """How long to wait before asking again: the server's Retry-After when it gave one (30 s at most), else 5 s, 10 s ..."""
    headers = getattr(exc, "headers", None)
    wait = headers.get("retry-after") if headers else None
    return min(30.0, float(wait) if wait and wait.isdigit() else 5.0 * (attempt + 1))


def _name(exc: BaseException, url: str, attempt: int) -> BaseException:
    """The same error, naming the URL (without its query) and the tries it took."""
    where = f"({url.split('?', 1)[0]}" + (f", {attempt + 1} tries)" if attempt else ")")
    if isinstance(exc, urllib.error.HTTPError):
        exc.msg = f"{exc.msg} {where}"
        return exc
    return AssetError(f"{type(exc).__name__}: {exc} {where}")


def _open(url: str, *, opener=None, timeout: float = 60.0, max_bytes: int = MAX_ASSET_BYTES, tries: int = 3) -> bytes:
    """GET an https URL. A busy or stumbling server's 429, 500, 502, 503 or 504, a read that timed out or a connection the
    line dropped is retried after its Retry-After (at most 30 s, ``tries`` times): Wikimedia asks every client to slow down
    rather than hammer it, and Commons and Openverse answer a 500 or hold a read now and then (F-15, F-17). The last error
    names the URL."""
    if not url.startswith("https://"):
        raise AssetError("only https URLs are allowed")
    request = urllib.request.Request(url, headers={"user-agent": USER_AGENT})
    for attempt in range(tries):
        try:
            with (opener or urllib.request.urlopen)(request, timeout=timeout) as response:
                data = response.read(max_bytes + 1)
            break
        except (urllib.error.URLError, OSError) as exc:          # HTTPError is a URLError; TimeoutError an OSError
            if not transient(exc) or attempt == tries - 1:
                raise _name(exc, url, attempt) from (None if isinstance(exc, urllib.error.HTTPError) else exc)
            time.sleep(transient_wait(exc, attempt))
    if len(data) > max_bytes:
        raise AssetError("asset is larger than the limit")
    return data


def _commons_candidate(page: dict) -> Candidate | None:
    info = (page.get("imageinfo") or [{}])[0]
    if not info:
        return None
    meta = info.get("extmetadata") or {}
    return Candidate(
        source="wikimedia_commons", title=page.get("title", ""), page_url=info.get("descriptionurl", ""),
        file_url=info.get("url", ""), thumb_url=info.get("thumburl") or info.get("url", ""),
        width=int(info.get("width") or 0), height=int(info.get("height") or 0), mime=info.get("mime", ""),
        licence=_strip_html((meta.get("LicenseShortName") or {}).get("value")),
        licence_url=_strip_html((meta.get("LicenseUrl") or {}).get("value")),
        author=_strip_html((meta.get("Artist") or {}).get("value"))[:300],
        credit=_strip_html((meta.get("Credit") or {}).get("value"))[:300])


def search_commons(query: str, *, limit: int = 12, thumb_width: int = 800, opener=None):
    """Image candidates from Wikimedia Commons that a lesson may use (licence policy, credit fields complete)."""
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": "6", "gsrlimit": str(limit),
              "gsrsearch": f"{query} filetype:bitmap|drawing", "prop": "imageinfo",
              "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(thumb_width)}
    raw = _open(COMMONS_API + "?" + urllib.parse.urlencode(params), opener=opener, max_bytes=8 * 1024 * 1024)
    pages = (json.loads(raw.decode("utf-8")).get("query") or {}).get("pages") or {}
    found = []
    for page in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        candidate = _commons_candidate(page)
        if candidate is None or candidate.mime not in IMAGE_TYPES or not lesson_ready(candidate):
            continue
        found.append(candidate)
    return found


COMMONS_THUMB_WIDTHS = (1920, 1280, 960, 500, 330, 250, 120)   # the sizes Wikimedia serves to scripts (https://w.wiki/GHai)


def commons_file(title: str, *, thumb_width: int = 1280, opener=None) -> Candidate:
    """One named Commons file ('File:...') with its licence as Commons states it (Task 046a, batch 3). The file to
    download is a thumbnail in one of Wikimedia's standard widths, the largest not above ``thumb_width`` and smaller than
    the original (Wikimedia answers scripted downloads of other sizes, and of originals, with 429); the page, author and
    licence stay the original's."""
    if not title.startswith("File:") or len(title) > 240:
        raise AssetError(f"{title!r} is not a Commons file title")
    widths = [w for w in COMMONS_THUMB_WIDTHS if w <= thumb_width] or [COMMONS_THUMB_WIDTHS[-1]]
    for width in widths:
        params = {"action": "query", "format": "json", "titles": title, "prop": "imageinfo",
                  "iiprop": "url|size|mime|extmetadata", "iiurlwidth": str(width)}
        raw = _open(COMMONS_API + "?" + urllib.parse.urlencode(params), opener=opener, max_bytes=4 * 1024 * 1024)
        body = json.loads(raw.decode("utf-8"))
        if "error" in body:                               # for example "ratelimited": said plainly, not as a missing file
            raise AssetError(f"Commons API refused {title!r}: {body['error'].get('code')}: {str(body['error'].get('info'))[:200]}")
        pages = (body.get("query") or {}).get("pages") or {}
        page = next(iter(pages.values()), {})
        candidate = _commons_candidate(page) if "missing" not in page else None
        if candidate is None:
            break
        if candidate.width and width >= candidate.width:  # Commons would hand back the original: ask for a smaller size
            continue
        url = candidate.thumb_url or candidate.file_url
        suffix = urllib.parse.urlparse(url).path.rsplit(".", 1)[-1].lower()   # Commons adds ?utm_source=... to its URLs
        mime = {"jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png", "webp": "image/webp"}.get(suffix, "")
        if mime:
            return Candidate(**{**candidate.__dict__, "file_url": url, "mime": mime})
        break
    raise AssetError(f"Commons has no picture {title!r} that BIE can draw")


def openverse_licence(code: str, version: str = "") -> str:
    name = OPENVERSE_LICENCES.get((code or "").lower(), code or "unknown")
    return f"{name} {version}".strip() if name.startswith("CC ") and version else name


def _openverse_candidate(row: dict) -> Candidate:
    licence = openverse_licence(row.get("license", ""), row.get("license_version") or "")
    ident = str(row.get("id", ""))
    return Candidate(
        source="openverse", title=row.get("title") or ident, page_url=row.get("foreign_landing_url") or "",
        # Openverse serves every image through its own thumbnail proxy (full size on request), one host for all providers
        file_url=f"{OPENVERSE_API}{ident}/thumb/?full_size=true", thumb_url=row.get("thumbnail") or "",
        width=int(row.get("width") or 0), height=int(row.get("height") or 0), mime="image/jpeg",
        licence=licence, licence_url=row.get("license_url") or "", author=(row.get("creator") or "")[:300],
        credit=(row.get("attribution") or f"{row.get('title')} by {row.get('creator')}, {licence}")[:400])


def search_openverse(query: str, *, limit: int = 12, opener=None) -> list:
    """Image candidates from Openverse (openly licensed works indexed from Flickr, Wikimedia, museums ...): only CC BY,
    CC0 and the Public Domain Mark are asked for, and every result is checked again against the licence policy."""
    params = {"q": query, "license": "by,cc0,pdm", "page_size": str(limit)}
    raw = _open(OPENVERSE_API + "?" + urllib.parse.urlencode(params), opener=opener, max_bytes=8 * 1024 * 1024)
    found = []
    for row in json.loads(raw.decode("utf-8")).get("results") or []:
        candidate = _openverse_candidate(row)
        if lesson_ready(candidate):
            found.append(candidate)
    return found


def openverse_image(identifier: str, *, opener=None) -> Candidate:
    """One Openverse image by its id, with its licence and attribution as Openverse records them."""
    if not re.fullmatch(r"[0-9a-f-]{36}", identifier or ""):
        raise AssetError(f"{identifier!r} is not an Openverse id")
    raw = _open(f"{OPENVERSE_API}{identifier}/", opener=opener, max_bytes=2 * 1024 * 1024)
    return _openverse_candidate(json.loads(raw.decode("utf-8")))


MET_API = "https://collectionapi.metmuseum.org/public/collection/v1/"
MET_LICENCE, MET_LICENCE_URL = "CC0 1.0", "https://creativecommons.org/publicdomain/zero/1.0/"


def _met_candidate(obj: dict) -> Candidate | None:
    """A Met Open Access object as a candidate: only public-domain objects (the Met releases them as CC0) with an image."""
    if not obj.get("isPublicDomain") or not (obj.get("primaryImageSmall") or obj.get("primaryImage")):
        return None
    title = str(obj.get("title") or obj.get("objectName") or f"Met object {obj.get('objectID')}")[:200]
    author = str(obj.get("artistDisplayName") or obj.get("culture") or "The Metropolitan Museum of Art")[:200]
    return Candidate(source="met_open_access", title=title, page_url=str(obj.get("objectURL") or ""),
                     file_url=str(obj.get("primaryImageSmall") or obj.get("primaryImage")), thumb_url=str(obj.get("primaryImageSmall") or ""),
                     width=0, height=0, mime="image/jpeg", licence=MET_LICENCE, licence_url=MET_LICENCE_URL, author=author,
                     credit=f"{title}, The Metropolitan Museum of Art, Open Access (CC0)")


def search_met(query: str, *, limit: int = 6, opener=None, lookups: int = 0) -> list:
    """Image candidates from The Met's Open Access collection (CC0, no key): coins, seals, weights and other objects of
    economic history (Task 046 Part D1). Objects not in the public domain are left out. Every object costs a request of its
    own, so at most ``lookups`` objects are read (default ``limit + 2``), each with a short timeout: the first live fetch of
    31 October 2026 spent its 30 minutes on up to 18 object reads per need."""
    params = {"hasImages": "true", "q": query}
    raw = _open(MET_API + "search?" + urllib.parse.urlencode(params), opener=opener, max_bytes=4 * 1024 * 1024, timeout=30.0, tries=2)
    ids = (json.loads(raw.decode("utf-8")).get("objectIDs") or [])[: lookups or limit + 2]
    found = []
    for oid in ids:
        if len(found) >= limit:
            break
        try:
            obj = json.loads(_open(f"{MET_API}objects/{int(oid)}", opener=opener, max_bytes=2 * 1024 * 1024,
                                   timeout=20.0, tries=2).decode("utf-8"))
        except (AssetError, ValueError, OSError):
            continue
        candidate = _met_candidate(obj)
        if candidate is not None and lesson_ready(candidate):
            found.append(candidate)
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
                      data: bytes | None = None) -> Asset:
        """A search result into the library, only when a lesson may use it (licence policy). ``data``: the file's bytes
        when the caller already has them (a cached download); otherwise they are fetched."""
        verdict = policy.asset_verdict(candidate)
        if not verdict.allowed:
            raise AssetError(f"{candidate.title}: licence {candidate.licence!r} is {verdict.text} for lessons: {verdict.reason}")
        data = data if data is not None else _open(candidate.file_url, opener=opener)
        return self.add_bytes(data, mime=candidate.mime, source=candidate.source, title=candidate.title,
                              page_url=candidate.page_url, licence=candidate.licence, licence_url=candidate.licence_url,
                              author=candidate.author, credit=candidate.credit, tags=list(tags), description=description)

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
        """Credit lines (title · author · licence (licence URL) · source page) for the outside assets among ``asset_ids``."""
        return policy.lesson_credits([self.assets[a] for a in asset_ids if a in self.assets])

    def lesson_check(self, asset_ids) -> list:
        """The lesson licence gate for these assets (``bie.toolbox.licence.lesson_licence_check``); an id the library does
        not hold is a problem too."""
        missing = [f"{a}: not in the asset library, so its licence cannot be read" for a in asset_ids if a not in self.assets]
        return missing + policy.lesson_licence_check([self.assets[a] for a in asset_ids if a in self.assets])

    def require_lesson(self, asset_ids, *, where: str = "lesson") -> list:
        """The hook a lesson output calls before it is rendered or packaged (the Task 046 director, the visual section,
        the game): raises ``bie.toolbox.licence.LicenceError`` with the problems, or returns the lesson's credits."""
        problems = self.lesson_check(asset_ids)
        if problems:
            raise policy.LicenceError(problems, where)
        return self.credits(asset_ids)


def seed_library(library: "AssetLibrary", source, *, opener=None) -> int:
    """Copy the assets of BIE's shared library (a folder, or an https base URL holding ``index.json`` and ``files/``; Task 046
    Part D1: the fetch step's images, licence-checked and credited) into ``library``; a file is fetched once and kept by hash.
    Returns how many assets were added. Every asset passes the licence policy again on the way in."""
    source = str(source).rstrip("/")
    remote = source.startswith("https://")
    raw = _open(source + "/index.json", opener=opener, max_bytes=4 * 1024 * 1024) if remote else (Path(source) / "index.json").read_bytes()
    added = 0
    for row in json.loads(raw.decode("utf-8")).get("assets", []):
        if row["asset_id"] in library.assets:
            continue
        if not re.fullmatch(r"files/[A-Za-z0-9._-]+", str(row.get("path") or "")) or ".." in row["path"]:
            continue                                                       # only a file of the library's own files/ folder
        verdict = policy.asset_verdict(Asset(**row))
        if not verdict.allowed:
            continue
        data = _open(source + "/" + row["path"], opener=opener) if remote else (Path(source) / row["path"]).read_bytes()
        if hashlib.sha256(data).hexdigest() != row["sha256"]:
            raise AssetError(f"{row['asset_id']}: the file does not match its recorded hash")
        library.add_bytes(data, mime=row["mime"], source=row["source"], title=row["title"], page_url=row["page_url"], licence=row["licence"],
                          licence_url=row["licence_url"], author=row["author"], credit=row["credit"], tags=row.get("tags") or [],
                          description=row.get("description", ""))
        added += 1
    return added
