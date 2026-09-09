def question(question_id,concept_id,prompt,options=None,answer=None,difficulty="FOUNDATION",
             rationale=""):
    return {"question_id":question_id,"concept_id":concept_id,"prompt":prompt,
            "options":options or [],"answer":answer,"difficulty":difficulty,
            "rationale":rationale}

def generate_diagnostic_questions(concept_id,concept_title):
    return [
      question(f"{concept_id}-D1",concept_id,f"What is the key idea of {concept_title}?",
               ["Definition","Unrelated fact"],"Definition","FOUNDATION",
               "Checks basic conceptual recognition."),
      question(f"{concept_id}-D2",concept_id,f"Which statement best applies to {concept_title}?",
               ["Core principle","Distractor"],"Core principle","INTERMEDIATE",
               "Checks conceptual application.")
    ]
