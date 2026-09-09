from ontology_extractor import make_learning_unit
from question_generator import generate_questions

def build_book_ontology(evidence_units):
    units=[]
    questions=[]
    for e in evidence_units:
        u=make_learning_unit(e["text"],e["evidence_id"])
        units.append(u)
        questions.extend(generate_questions(e["text"]))
    return {
      "schema_version":"3.1",
      "units":units,
      "question_bank":questions,
      "coverage_policy":{
        "axes":["what","who","when","where","why","how","which","how_much"],
        "book_wide":True,
        "missing_axes_must_be_marked":"NOT_APPLICABLE_OR_NOT_FOUND"
      }
    }
