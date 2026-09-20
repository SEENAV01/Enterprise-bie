#!/usr/bin/env python3
"""Trusted deterministic worker: request JSON -> real existing-emitter source tree."""
from dataclasses import asdict
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from bie.compiler.qa_scene_compile import compile_scene_for_qa, CompilerQATarget
from bie.compiler.deterministic_codegen import write_codegen_plan
from bie.compiler.qa_common import write_json


def main() -> int:
    if len(sys.argv) != 3:
        raise ValueError("usage: qa_compile_worker.py request.json empty-output-directory")
    request = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    root = Path(sys.argv[2])
    if root.is_symlink() or (root.exists() and any(root.iterdir())):
        raise ValueError("worker output must be empty and non-symlink")
    bundle = compile_scene_for_qa(request["document"], target=CompilerQATarget(**request.get("target", {})))
    write_codegen_plan(bundle.codegen, root)
    write_json(root / "SOURCE_MAP.json", asdict(bundle.source_map))
    # Findings are deterministic source evidence. This worker is not a quality-gate pass signal.
    write_json(root / "SOURCE_CONTRACT.json", {"findings": [asdict(f) for f in bundle.findings],
                    "passed": bundle.source_contract_passed, "accepted": False})
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
