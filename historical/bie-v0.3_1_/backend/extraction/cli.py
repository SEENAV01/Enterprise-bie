from __future__ import annotations
import argparse, json
from .m3_extractor import extract_with_openai

p = argparse.ArgumentParser(description="BIE M3 semantic extraction")
p.add_argument("input_json", help="M2 document JSON")
p.add_argument("output_json")
p.add_argument("--model", default=None)
args = p.parse_args()
with open(args.input_json, encoding="utf-8") as f:
    doc = json.load(f)
blocks = doc.get("blocks", doc.get("pages", []))
result = extract_with_openai(blocks, args.model)
with open(args.output_json, "w", encoding="utf-8") as f:
    json.dump({"units": result.units, "relations": result.relations, "warnings": result.warnings}, f, ensure_ascii=False, indent=2)
print(f"units={len(result.units)} relations={len(result.relations)} warnings={len(result.warnings)}")
