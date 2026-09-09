from objectives import objective, valid as objective_valid
from pedagogy import strategy, valid as strategy_valid
from assessment import assessment, aligned as assessment_aligned
from curriculum import unit, valid as unit_valid
from lesson import lesson_plan, aligned as lesson_aligned
from alignment import alignment_record, valid as alignment_valid
from provenance import provenance, traceable
from verification import verification, passed

def build_pedagogy_curriculum():
    o1 = objective("obj-charge", "Explain electric charge", "UNDERSTAND",
                   ["ev-charge"])
    o2 = objective("obj-force", "Predict electric force direction", "APPLY",
                   ["ev-force"])

    s1 = strategy("str-1", "EXPLANATION", ["obj-charge"],
                  "Build the foundational concept before application.")
    s2 = strategy("str-2", "DEMONSTRATION", ["obj-force"],
                  "Connect the force rule to a concrete visual example.")

    a1 = assessment("assess-1", "FORMATIVE", ["obj-charge"],
                    ["Learner correctly defines charge."])
    a2 = assessment("assess-2", "APPLICATION", ["obj-force"],
                    ["Learner correctly predicts force direction."])

    u1 = unit("unit-1", "Electric Charge and Force",
              ["obj-charge", "obj-force"], [], ["lesson-1"])

    lp = lesson_plan("lesson-1", "Charge to Electric Force",
                     ["obj-charge", "obj-force"],
                     ["str-1", "str-2"],
                     ["assess-1", "assess-2"],
                     ["c-charge"], 12)

    ar = alignment_record("align-1",
                          lp["objective_ids"],
                          lp["strategy_ids"],
                          lp["assessment_ids"],
                          ["ev-charge", "ev-force"])

    prov = provenance("lesson-1", ["book-1"],
                       ["lg-1", "kg-1"],
                       ["ev-charge", "ev-force"],
                       ["artifact://learning-graph"])

    check = verification("verify-1", "lesson-1", "PASS",
                         ["ev-charge", "ev-force"])

    return {
        "schema_version": "6.52",
        "objectives": [o1, o2],
        "strategies": [s1, s2],
        "assessments": [a1, a2],
        "units": [u1],
        "lesson_plan": lp,
        "alignment": ar,
        "provenance": prov,
        "verification": check,
        "quality_gate": {
            "valid": (
                objective_valid(o1) and objective_valid(o2)
                and strategy_valid(s1) and strategy_valid(s2)
                and assessment_aligned(a1) and assessment_aligned(a2)
                and unit_valid(u1) and lesson_aligned(lp)
                and alignment_valid(ar) and traceable(prov)
                and passed(check)
            ),
            "errors": []
        }
    }
