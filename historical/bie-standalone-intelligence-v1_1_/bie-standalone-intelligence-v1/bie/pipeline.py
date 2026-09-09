from pathlib import Path
import json
from dataclasses import asdict

class BIEPipeline:
    """
    Standalone orchestration shell for the existing intelligence.
    Boundary: source book -> validated video-generation code.
    Rendering is intentionally outside this package.
    """
    def __init__(self, workspace="output"):
        self.workspace = Path(workspace)

    def initialize(self, book_path):
        self.workspace.mkdir(parents=True, exist_ok=True)
        state = {
            "book_path": str(Path(book_path)),
            "status": "initialized",
            "stages": [
                "ingest",
                "document_structure",
                "knowledge_extraction",
                "concept_graph",
                "prerequisite_graph",
                "course_planning",
                "lesson_planning",
                "scene_planning",
                "visual_planning",
                "code_generation",
                "static_validation"
            ],
            "boundary": "validated_video_generation_code"
        }
        (self.workspace / "run_state.json").write_text(
            json.dumps(state, indent=2), encoding="utf-8"
        )
        return state

    def status(self):
        p=self.workspace/"run_state.json"
        return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None
