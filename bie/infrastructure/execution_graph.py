"""Governed v2 graph: Math is mandatory before Reasoning.

Byte-exact v1 pins historical profiles. Audio reconciliation remains open.
"""
from dataclasses import dataclass
from . import execution_graph_v1 as v1

EnterpriseGraphError = v1.EnterpriseGraphError
STAGES = v1.STAGES | {"MATH"}


@dataclass(frozen=True)
class StageContract(v1.StageContract):
    def validate(self):
        if self.stage_id not in STAGES or not self.emits:
            raise EnterpriseGraphError("invalid v2 stage contract")
        if any(p not in STAGES for p in self.required_predecessors):
            raise EnterpriseGraphError("unknown v2 predecessor")


@dataclass
class EnterpriseExecutionGraph(v1.EnterpriseExecutionGraph):
    def _assert_mandatory_paths(self):
        super()._assert_mandatory_paths()
        m = self.stages.get("MATH")
        r = self.stages.get("REASONING")
        if m is None or r is None:
            raise EnterpriseGraphError("v2 requires Math before Reasoning")
        if (m.consumes != ["document.structured", "knowledge.graph", "prerequisite.graph"]
                or m.emits != "math.evidence"
                or m.required_predecessors != ["DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE"]
                or r.consumes != ["knowledge.graph", "prerequisite.graph", "math.evidence"]
                or r.required_predecessors != ["KNOWLEDGE", "PREREQUISITE", "MATH"]):
            raise EnterpriseGraphError("Math artifact dependency bypass")
        if not self._direct_edge("PREREQUISITE", "MATH") or not self._direct_edge("MATH", "REASONING"):
            raise EnterpriseGraphError("Math execution path bypass")
        for source, targets in self.edges.items():
            if "REASONING" in targets and source != "MATH":
                raise EnterpriseGraphError("Reasoning path bypasses Math")
        for stage in self.stages.values():
            if any(p not in self.stages for p in stage.required_predecessors):
                raise EnterpriseGraphError("missing stage dependency")


def legacy_enterprise_graph_v1():
    """Explicit immutable architectural contract for Tasks029/030."""
    return v1.default_enterprise_graph()


def default_enterprise_graph():
    old = legacy_enterprise_graph_v1()
    contracts = {}
    for key, c in old.stages.items():
        if key == "REASONING":
            contracts["MATH"] = StageContract("MATH",
                ["document.structured", "knowledge.graph", "prerequisite.graph"], "math.evidence",
                ["DOCUMENT_INTELLIGENCE", "KNOWLEDGE", "PREREQUISITE"], True)
            contracts[key] = StageContract(key, ["knowledge.graph", "prerequisite.graph", "math.evidence"],
                c.emits, ["KNOWLEDGE", "PREREQUISITE", "MATH"])
        else:
            contracts[key] = StageContract(c.stage_id, list(c.consumes), c.emits,
                list(c.required_predecessors), c.evidence_producer, c.legacy_adapter)
    edges = {s:[t for t in ts if t != "REASONING"] for s, ts in old.edges.items()}
    edges["PREREQUISITE"].append("MATH")
    edges["MATH"] = ["REASONING"]
    graph = EnterpriseExecutionGraph(contracts, edges)
    graph.validate()
    return graph
