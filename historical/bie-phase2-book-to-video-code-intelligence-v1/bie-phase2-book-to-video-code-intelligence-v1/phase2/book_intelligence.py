from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import json

@dataclass
class SourceBlock:
    id: str
    page_start: int
    page_end: int
    text: str
    heading: Optional[str] = None

@dataclass
class Concept:
    id: str
    name: str
    explanation: str
    source_blocks: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)
    formulas: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)

@dataclass
class LessonSpec:
    id: str
    title: str
    objective: str
    concept_ids: List[str]
    sequence: List[str]
    estimated_minutes: float

@dataclass
class SceneSpec:
    id: str
    lesson_id: str
    purpose: str
    narration: str
    visual_type: str
    concept_ids: List[str]
    source_blocks: List[str] = field(default_factory=list)
    assets: List[str] = field(default_factory=list)

@dataclass
class VideoCodeSpec:
    lesson_id: str
    scenes: List[SceneSpec]
    runtime_contract: Dict[str, Any]

class BookToVideoPlanner:
    """
    Phase 2 intelligence boundary:
    PDF/source -> structured book model -> course/lesson plan ->
    scene plan -> deterministic video-code specification.

    It intentionally stops BEFORE rendering, execution and QA.
    """

    def build_book_model(self, blocks: List[SourceBlock]) -> Dict[str, Any]:
        return {
            "source_blocks": [b.__dict__ for b in blocks],
            "concepts": [],
            "chapters": [],
            "cross_references": [],
            "open_questions": []
        }

    def build_lesson_specs(self, book_model: Dict[str, Any]) -> List[LessonSpec]:
        # Planner implementation is model/provider supplied.
        raise NotImplementedError("Connect the document/pedagogy planner here.")

    def build_scene_specs(self, lesson: LessonSpec,
                          concepts: List[Concept]) -> List[SceneSpec]:
        raise NotImplementedError("Connect the scene planner here.")

    def build_video_code_spec(self, lesson: LessonSpec,
                              scenes: List[SceneSpec]) -> VideoCodeSpec:
        return VideoCodeSpec(
            lesson_id=lesson.id,
            scenes=scenes,
            runtime_contract={
                "renderer": "remotion",
                "resolution": [1920,1080],
                "fps": 30,
                "code_only": True
            }
        )

    def export_code_generation_input(self, spec: VideoCodeSpec) -> str:
        return json.dumps({
            "lesson_id": spec.lesson_id,
            "scenes": [s.__dict__ for s in spec.scenes],
            "runtime_contract": spec.runtime_contract
        }, indent=2)
