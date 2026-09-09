from dataclasses import dataclass

@dataclass
class EvaluationResult:
    coverage: float
    grounding: float
    relation_accuracy: float
    dependency_accuracy: float
    pedagogical_quality: float
    issues: list[str]

    @property
    def overall(self):
        weights = {
            "coverage": .20, "grounding": .25, "relation_accuracy": .15,
            "dependency_accuracy": .20, "pedagogical_quality": .20
        }
        return sum(getattr(self, k) * w for k, w in weights.items())

def evaluate(candidate_units, source_units, candidate_relationships, source_relationships):
    src_ids = {u.id for u in source_units}
    cand_ids = {u.id for u in candidate_units}
    coverage = len(cand_ids & src_ids) / max(1, len(src_ids))
    src_rels = {(r.source, r.relation, r.target) for r in source_relationships}
    cand_rels = {(r.source, r.relation, r.target) for r in candidate_relationships}
    relation_accuracy = len(cand_rels & src_rels) / max(1, len(cand_rels))
    grounding = sum(1 for u in candidate_units if u.source.page > 0) / max(1, len(candidate_units))
    return EvaluationResult(coverage, grounding, relation_accuracy, 1.0, 1.0, [])
