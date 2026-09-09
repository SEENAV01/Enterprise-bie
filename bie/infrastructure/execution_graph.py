from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Set, Optional

class EnterpriseGraphError(ValueError):
    pass

STAGES = {
    "SOURCE","DOCUMENT_INTELLIGENCE","KNOWLEDGE","PREREQUISITE","REASONING",
    "PEDAGOGY","DIRECTOR","VISUAL","ANIMATION","SCENE_IR","VIDEO_CODE",
    "VIDEO_COMPILE","VIDEO_RENDER","VIDEO_QA","GAME_DIRECTOR","GAME_IR",
    "GAME_CODE","GAME_BUILD","GAME_RUNTIME","GAME_QA","LINEAGE_QA",
    "REGRESSION_QA","REPRODUCIBILITY_QA","RELEASE_EVALUATION","RELEASE_MANIFEST"
}

@dataclass(frozen=True)
class StageContract:
    stage_id:str
    consumes:List[str]
    emits:str
    required_predecessors:List[str]=field(default_factory=list)
    evidence_producer:bool=False
    legacy_adapter:Optional[str]=None

    def validate(self)->None:
        if self.stage_id not in STAGES:
            raise EnterpriseGraphError(f"unknown stage {self.stage_id}")
        if not self.emits:
            raise EnterpriseGraphError("stage must emit typed artifact")
        for p in self.required_predecessors:
            if p not in STAGES:
                raise EnterpriseGraphError(f"unknown predecessor {p}")

@dataclass
class EnterpriseExecutionGraph:
    stages:Dict[str,StageContract]
    edges:Dict[str,List[str]]

    def validate(self)->None:
        for s in self.stages.values(): s.validate()
        for src,targets in self.edges.items():
            if src not in self.stages: raise EnterpriseGraphError(f"edge source missing {src}")
            for t in targets:
                if t not in self.stages: raise EnterpriseGraphError(f"edge target missing {t}")
        self._assert_acyclic()
        self._assert_mandatory_paths()

    def _assert_acyclic(self)->None:
        visiting,visited=set(),set()
        def dfs(n):
            if n in visiting: raise EnterpriseGraphError("cycle in enterprise execution graph")
            if n in visited:return
            visiting.add(n)
            for x in self.edges.get(n,[]):dfs(x)
            visiting.remove(n);visited.add(n)
        for n in self.stages:dfs(n)

    def _reachable(self,start:str,target:str)->bool:
        seen=set(); stack=[start]
        while stack:
            n=stack.pop()
            if n==target:return True
            if n in seen:continue
            seen.add(n);stack.extend(self.edges.get(n,[]))
        return False

    def _direct_edge(self,a,b)->bool:
        return b in self.edges.get(a,[])

    def _assert_mandatory_paths(self)->None:
        # Architectural anti-bypass rules.
        if self._direct_edge("SOURCE","VIDEO_CODE"):
            raise EnterpriseGraphError("raw source cannot directly generate video code")
        if self._direct_edge("SOURCE","GAME_CODE"):
            raise EnterpriseGraphError("raw source cannot directly generate game code")
        if not self._reachable("REASONING","SCENE_IR"):
            raise EnterpriseGraphError("Scene IR must be downstream of reasoning")
        if not self._reachable("SCENE_IR","VIDEO_CODE"):
            raise EnterpriseGraphError("video code must be downstream of Scene IR")
        if not self._reachable("REASONING","GAME_IR"):
            raise EnterpriseGraphError("Game IR must be downstream of reasoning")
        if not self._reachable("GAME_IR","GAME_CODE"):
            raise EnterpriseGraphError("game code must be downstream of Game IR")
        for required in ["VIDEO_QA","GAME_QA","LINEAGE_QA","REGRESSION_QA","REPRODUCIBILITY_QA"]:
            if not self._reachable(required,"RELEASE_EVALUATION"):
                raise EnterpriseGraphError(f"{required} must feed release evaluation")
        if not self._reachable("RELEASE_EVALUATION","RELEASE_MANIFEST"):
            raise EnterpriseGraphError("release manifest must derive from release evaluation")

def default_enterprise_graph()->EnterpriseExecutionGraph:
    def S(stage,consumes,emits,preds=None,evidence=False,legacy=None):
        return StageContract(stage,consumes,emits,preds or [],evidence,legacy)

    ss=[
      S("SOURCE",[],"source.document"),
      S("DOCUMENT_INTELLIGENCE",["source.document"],"document.structured",["SOURCE"],legacy="document_ingestor.py"),
      S("KNOWLEDGE",["document.structured"],"knowledge.graph",["DOCUMENT_INTELLIGENCE"],legacy="concept_understanding.py"),
      S("PREREQUISITE",["knowledge.graph"],"prerequisite.graph",["KNOWLEDGE"],legacy="concept_understanding.py"),
      S("REASONING",["knowledge.graph","prerequisite.graph"],"reasoning.decision_set",["KNOWLEDGE","PREREQUISITE"]),
      S("PEDAGOGY",["reasoning.decision_set"],"pedagogy.plan",["REASONING"],legacy="lesson_planner.py"),
      S("DIRECTOR",["pedagogy.plan","reasoning.decision_set"],"director.plan",["PEDAGOGY","REASONING"],legacy="script_compiler.py"),
      S("VISUAL",["director.plan","reasoning.decision_set"],"visual.plan",["DIRECTOR","REASONING"]),
      S("ANIMATION",["visual.plan","director.plan"],"animation.plan",["VISUAL","DIRECTOR"]),
      S("SCENE_IR",["visual.plan","animation.plan","director.plan"],"scene.ir",["VISUAL","ANIMATION"],legacy="scene_dsl.py"),
      S("VIDEO_CODE",["scene.ir"],"code.video_bundle",["SCENE_IR"],legacy="remotion_generator.py"),
      S("VIDEO_COMPILE",["code.video_bundle"],"evidence.video_compile",["VIDEO_CODE"],True),
      S("VIDEO_RENDER",["code.video_bundle","evidence.video_compile"],"evidence.video_render",["VIDEO_COMPILE"],True),
      S("VIDEO_QA",["evidence.video_render","scene.ir"],"qa.video",["VIDEO_RENDER","SCENE_IR"],True),
      S("GAME_DIRECTOR",["reasoning.decision_set","pedagogy.plan"],"game.plan",["REASONING","PEDAGOGY"],legacy="game_generator.py"),
      S("GAME_IR",["game.plan"],"game.ir",["GAME_DIRECTOR"]),
      S("GAME_CODE",["game.ir"],"code.game_bundle",["GAME_IR"]),
      S("GAME_BUILD",["code.game_bundle"],"evidence.game_build",["GAME_CODE"],True),
      S("GAME_RUNTIME",["code.game_bundle","evidence.game_build"],"evidence.game_runtime",["GAME_BUILD"],True),
      S("GAME_QA",["game.ir","evidence.game_runtime"],"qa.game",["GAME_RUNTIME","GAME_IR"],True),
      S("LINEAGE_QA",["*"],"qa.lineage",[],True),
      S("REGRESSION_QA",["*"],"qa.regression",[],True),
      S("REPRODUCIBILITY_QA",["*"],"qa.reproducibility",[],True),
      S("RELEASE_EVALUATION",["qa.video","qa.game","qa.lineage","qa.regression","qa.reproducibility"],"release.decision",
        ["VIDEO_QA","GAME_QA","LINEAGE_QA","REGRESSION_QA","REPRODUCIBILITY_QA"],True),
      S("RELEASE_MANIFEST",["release.decision"],"release.manifest",["RELEASE_EVALUATION"])
    ]
    stages={s.stage_id:s for s in ss}
    edges={
      "SOURCE":["DOCUMENT_INTELLIGENCE"],
      "DOCUMENT_INTELLIGENCE":["KNOWLEDGE"],
      "KNOWLEDGE":["PREREQUISITE","REASONING"],
      "PREREQUISITE":["REASONING"],
      "REASONING":["PEDAGOGY"],
      "PEDAGOGY":["DIRECTOR","GAME_DIRECTOR"],
      "DIRECTOR":["VISUAL"],
      "VISUAL":["ANIMATION"],
      "ANIMATION":["SCENE_IR"],
      "SCENE_IR":["VIDEO_CODE","VIDEO_QA"],
      "VIDEO_CODE":["VIDEO_COMPILE"],
      "VIDEO_COMPILE":["VIDEO_RENDER"],
      "VIDEO_RENDER":["VIDEO_QA"],
      "GAME_DIRECTOR":["GAME_IR"],
      "GAME_IR":["GAME_CODE","GAME_QA"],
      "GAME_CODE":["GAME_BUILD"],
      "GAME_BUILD":["GAME_RUNTIME"],
      "GAME_RUNTIME":["GAME_QA"],
      "VIDEO_QA":["RELEASE_EVALUATION"],
      "GAME_QA":["RELEASE_EVALUATION"],
      "LINEAGE_QA":["RELEASE_EVALUATION"],
      "REGRESSION_QA":["RELEASE_EVALUATION"],
      "REPRODUCIBILITY_QA":["RELEASE_EVALUATION"],
      "RELEASE_EVALUATION":["RELEASE_MANIFEST"]
    }
    g=EnterpriseExecutionGraph(stages,edges);g.validate();return g
