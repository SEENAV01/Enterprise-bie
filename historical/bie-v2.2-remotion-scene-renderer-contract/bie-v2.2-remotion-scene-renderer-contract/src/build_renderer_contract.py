import json,sys
from pathlib import Path
from scene_compiler import compile_lesson
from remotion_manifest import build_manifest

if __name__=="__main__":
    lesson=json.loads(Path(sys.argv[1]).read_text())
    compiled=compile_lesson(lesson)
    manifest=build_manifest(compiled)
    result={"scene_dsl":compiled,"remotion_manifest":manifest}
    Path(sys.argv[2]).write_text(json.dumps(result,indent=2,ensure_ascii=False))
