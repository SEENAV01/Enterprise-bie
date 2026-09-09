import json, sys
from pathlib import Path
from structure import build_heading_tree, attach_parents
from assets import collect_assets
from hierarchical import make_chapter_units, consolidation_plan

def run(path,out):
    pages=json.loads(Path(path).read_text())
    pages=attach_parents(pages)
    result={
        "schema_version":"1.8",
        "pages":pages,
        "heading_tree":build_heading_tree(pages),
        "assets":collect_assets(pages),
        "chapter_units":make_chapter_units(pages)
    }
    result["consolidation_batches"]=consolidation_plan(result["chapter_units"])
    Path(out).write_text(json.dumps(result,indent=2,ensure_ascii=False))
    return result

if __name__=="__main__":
    run(sys.argv[1],sys.argv[2])
