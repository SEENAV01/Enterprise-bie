import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from objectives import objective, valid
from pedagogy import strategy
from assessment import assessment, aligned
from curriculum import unit
from lesson import lesson_plan, aligned as lesson_aligned
from alignment import alignment_record, valid as alignment_valid
from provenance import provenance, traceable
from verification import verification, passed

def test_objective_strategy_assessment():
    o = objective("o","Explain","UNDERSTAND",["e"])
    s = strategy("s","EXPLANATION",["o"])
    a = assessment("a","FORMATIVE",["o"],["Correct response"])
    assert valid(o) and s["objective_ids"] == ["o"] and aligned(a)

def test_lesson_alignment():
    u = unit("u","Unit",["o"],[],["l"])
    l = lesson_plan("l","Lesson",["o"],["s"],["a"])
    ar = alignment_record("ar",["o"],["s"],["a"],["e"])
    p = provenance("l",["source"],["lg"],["e"])
    v = verification("v","l","PASS",["e"])
    assert u["lesson_ids"] == ["l"]
    assert lesson_aligned(l) and alignment_valid(ar)
    assert traceable(p) and passed(v)
