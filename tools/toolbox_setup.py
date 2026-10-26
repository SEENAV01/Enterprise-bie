"""Install the toolbox's web packages (Task 046a), pinned, as of the date in tools/npm_before.txt.

    python tools/toolbox_setup.py --web <folder>        npm install every group of bie/toolbox/web_packages.json there
    python tools/toolbox_setup.py --print-env <folder>  the NODE_PATH and ESBUILD lines for the preview renderer
    python tools/toolbox_setup.py --assets <folder>     fetch the downloads a demo needs from a flaky server into an
                                                        asset cache folder (CI saves it on main for every PR, F-13)

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


def prefetch_assets(cache: Path, *, opener=None, sleep=time.sleep) -> dict:
    """The SRTM15+ tables and tiles of the geo-relief demo, from GMT's one data server, into ``cache``/gmt: the server
    was unreachable from GitHub's runners for minutes at a time (F-13), and a PR's own cache starts empty."""
    from bie.toolbox.adapters import earth
    folder = Path(cache) / "gmt"
    folder.mkdir(parents=True, exist_ok=True)
    return {"gmt_relief": earth.prefetch_relief(earth.DEFAULT_RESOLUTION, earth.DEFAULT_REGION, userdir=folder, opener=opener,
                                                sleep=sleep)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--web", type=Path)
    parser.add_argument("--groups", default="", help="comma list of groups (default: all)")
    parser.add_argument("--print-env", type=Path)
    parser.add_argument("--assets", type=Path)
    args = parser.parse_args(argv)
    if args.web:
        install(args.web, [g for g in args.groups.split(",") if g] or None)
    if args.print_env:
        modules = args.print_env.resolve() / "node_modules"
        print(f"NODE_PATH={modules}")
        print(f"ESBUILD={modules / 'esbuild' / 'bin' / 'esbuild'}")
    if args.assets:
        print(json.dumps(prefetch_assets(args.assets), indent=1))
    if not (args.web or args.print_env or args.assets):
        parser.print_help()
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
