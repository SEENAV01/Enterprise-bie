def question(question_id,concept_id,prompt,response_type,
              correct_answer=None,rubric=None,difficulty=None,hints=None):
    return {"question_id":question_id,"concept_id":concept_id,"prompt":prompt,
            "response_type":response_type,"correct_answer":correct_answer,
            "rubric":rubric,"difficulty":difficulty,"hints":hints or []}
