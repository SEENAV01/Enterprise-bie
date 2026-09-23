"""Check merged debug/release network policy after Android manifest processing."""

from __future__ import annotations

from pathlib import Path
import sys
import xml.etree.ElementTree as ET


ANDROID = "{http://schemas.android.com/apk/res/android}"
ROOT = Path(__file__).resolve().parents[3]
INTERMEDIATES = ROOT / "apps/android/app/build/intermediates"


def manifests_for(variant: str) -> list[Path]:
    return [
        path for path in INTERMEDIATES.rglob("AndroidManifest.xml")
        if variant in path.parts and any("merged_manifest" in part for part in path.parts)
    ]


def main() -> int:
    evidence = Path(sys.argv[1])
    lines = []
    for variant, cleartext in (("debug", "true"), ("release", "false")):
        paths = manifests_for(variant)
        if not paths:
            raise RuntimeError(f"merged {variant} manifest missing")
        for path in paths:
            root = ET.parse(path).getroot()
            application = root.find("application")
            if application is None or application.get(ANDROID + "usesCleartextTraffic") != cleartext:
                raise RuntimeError(f"{variant} cleartext policy mismatch")
            permissions = {
                element.get(ANDROID + "name") for element in root.findall("uses-permission")
            }
            if "android.permission.INTERNET" not in permissions:
                raise RuntimeError(f"{variant} INTERNET permission missing")
        lines.append(f"{variant}: INTERNET present; cleartext={cleartext}")
    evidence.mkdir(parents=True, exist_ok=True)
    (evidence / "manifest-security-summary.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("Merged Android manifest policies: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
