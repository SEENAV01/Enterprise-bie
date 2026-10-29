"""Install the toolbox's web packages (Task 046a), pinned, as of the date in tools/npm_before.txt.

    python tools/toolbox_setup.py --web <folder>        npm install every group of bie/toolbox/web_packages.json there
    python tools/toolbox_setup.py --print-env <folder>  the NODE_PATH and ESBUILD lines for the preview renderer
    python tools/toolbox_setup.py --assets <folder>     fetch the downloads a demo needs from a flaky server into an
                                                        asset cache folder (CI saves it on main for every PR, F-13, F-16)
    python tools/toolbox_setup.py --skyfield <folder>   only the skyfield files, from CDS or a VizieR mirror (F-16)
    python tools/toolbox_setup.py --archive-images <folder>   only the archive demo's two pictures (Commons, Openverse; F-17b)

Python libraries come from pyproject extras (pip install -e '.[toolbox-core,toolbox-bio,...]'); system libraries for
Manim (Cairo, Pango) from apt; neither is installed by this script.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
PACKAGES = ROOT / "bie" / "toolbox" / "web_packages.json"


def specs(groups=None) -> list:
    data = json.loads(PACKAGES.read_text(encoding="utf-8"))
    chosen = groups or list(data["groups"])
    return [f"{name}@{version}" for g in chosen for name, version in data["groups"][g].items()]


def before() -> str:
    return (ROOT / json.loads(PACKAGES.read_text(encoding="utf-8"))["npm_before_file"]).read_text(encoding="utf-8").strip()


def install(folder: Path, groups=None) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    if not (folder / "package.json").exists():
        (folder / "package.json").write_text('{"name": "bie-toolbox-web", "private": true}\n', encoding="utf-8")
    cmd = ["npm", "install", "--no-audit", "--no-fund", "--ignore-scripts", "--before", before(), *specs(groups)]
    subprocess.run(cmd, cwd=folder, check=True)
    subprocess.run(["node", "node_modules/esbuild/install.js"], cwd=folder, check=False)


def prefetch_skyfield(cache: Path, *, opener=None, sleep=time.sleep, tries: int = 3, wait: float = 10.0) -> dict:
    """The two files the astro demos need, into ``cache``/skyfield where ``adapters.astro._loader`` looks for them by name:
    JPL's DE421 ephemeris (17 MB, NAIF) and the Hipparcos catalogue (51 MB, CDS). Skyfield's own loader downloads a missing
    file on the spot, so without this the demos fetched both from the two servers on every run; CDS timed out from GitHub's
    runners on 27 October 2026 (F-16). A file already here is kept; an unreachable server is recorded, never raised, so the
    other files still reach the cache."""
    from bie.toolbox.adapters import astro, earth
    folder = Path(cache) / "skyfield"
    folder.mkdir(parents=True, exist_ok=True)
    done = {}
    files = ((astro.EPHEMERIS["file"], (astro.EPHEMERIS["source"],)),
             (astro.BSC["file"], (astro.BSC["source"], *astro.BSC.get("mirrors", ()))),
             ("hip_main.dat", (astro.HIPPARCOS["source"], *astro.HIPPARCOS.get("mirrors", ()))))
    for name, urls in files:
        path = folder / name
        if path.exists() and path.stat().st_size > 0:
            done[name] = "cached"
            continue
        errors = []
        for url in urls:                                    # the canonical server first, then its mirrors (the same file)
            try:
                data = earth._download(url, opener=opener, tries=tries, wait=wait, sleep=sleep, timeout=300.0)
            except Exception as exc:                        # noqa: BLE001 - the cache job must save what it did fetch
                errors.append(f"{url.split('/')[2]}: {str(exc).split(': ', 1)[-1]}"[:160])     # the host and the error, not the URL twice
                continue
            tmp = path.with_suffix(path.suffix + ".part")
            tmp.write_bytes(data)
            tmp.replace(path)
            done[name] = "fetched" if url == urls[0] else f"fetched from {url}"
            break
        else:
            done[name] = "unreachable: " + " | ".join(errors)
    return done


def prefetch_archive_images(cache: Path, *, opener=None) -> dict:
    """The archive demo's two pictures (Wikimedia Commons, Openverse) into ``cache``/open-images, where ``sources._open_image``
    reads them before asking the archive (F-17b: Openverse answered 500 three times in a row, Commons let a read time out;
    a demo run should not depend on either being up). A picture that cannot be fetched is reported, not raised: the demo
    job fetches it itself then, as before."""
    import os
    import tempfile
    from bie.brain.assets import AssetLibrary
    from bie.toolbox import demos, sources
    os.environ["BIE_ASSET_CACHE"] = str(cache)
    done = {}
    with tempfile.TemporaryDirectory() as scratch:
        library = AssetLibrary(Path(scratch) / "library")
        for name, fetch in (("commons", lambda: sources.commons_image(demos.SALT_MARCH_COMMONS, library, width=demos.SALT_MARCH_WIDTH, opener=opener)),
                            ("openverse", lambda: sources.openverse_image(demos.SALT_MARCH_OPENVERSE, library, opener=opener))):
            try:
                fetch()
                done[name] = "fetched"
            except Exception as exc:                           # noqa: BLE001  (reported in the job's output, never fatal here)
                done[name] = f"failed: {type(exc).__name__}: {str(exc)[:160]}"
    return done


def prefetch_assets(cache: Path, *, opener=None, sleep=time.sleep) -> dict:
    """The downloads the demos need from flaky servers, into ``cache``: the SRTM15+ tables and tiles of the geo-relief demo
    from GMT's one data server (``cache``/gmt; unreachable from GitHub's runners for minutes at a time, F-13), the
    skyfield files of the astro demos (``cache``/skyfield; CDS timed out, F-16) and the archive demo's two pictures
    (``cache``/open-images; Openverse answered 500, F-17b). A PR's own cache starts empty; the cache saved on main is what
    every PR restores."""
    from bie.toolbox.adapters import earth
    folder = Path(cache) / "gmt"
    folder.mkdir(parents=True, exist_ok=True)
    return {"gmt_relief": earth.prefetch_relief(earth.DEFAULT_RESOLUTION, earth.DEFAULT_REGION, userdir=folder, opener=opener,
                                                sleep=sleep),
            "skyfield": prefetch_skyfield(cache, opener=opener, sleep=sleep),
            "archive_images": prefetch_archive_images(cache, opener=opener)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--web", type=Path)
    parser.add_argument("--groups", default="", help="comma list of groups (default: all)")
    parser.add_argument("--print-env", type=Path)
    parser.add_argument("--assets", type=Path)
    parser.add_argument("--skyfield", type=Path, help="only the skyfield files (the batch-2 demos job runs this after its cache restore, F-16)")
    parser.add_argument("--archive-images", type=Path, help="only the archive demo's pictures (the batch-3 demos job runs this after its cache "
                                                             "restore, F-17b); a picture the archive cannot give is reported, not fatal")
    args = parser.parse_args(argv)
    if args.web:
        install(args.web, [g for g in args.groups.split(",") if g] or None)
    if args.print_env:
        modules = args.print_env.resolve() / "node_modules"
        print(f"NODE_PATH={modules}")
        print(f"ESBUILD={modules / 'esbuild' / 'bin' / 'esbuild'}")
    if args.assets:
        print(json.dumps(prefetch_assets(args.assets), indent=1))
    if args.skyfield:
        print(json.dumps({"skyfield": prefetch_skyfield(args.skyfield)}, indent=1))
    if args.archive_images:
        print(json.dumps({"archive_images": prefetch_archive_images(args.archive_images)}, indent=1))
    if not (args.web or args.print_env or args.assets or args.skyfield or args.archive_images):
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
