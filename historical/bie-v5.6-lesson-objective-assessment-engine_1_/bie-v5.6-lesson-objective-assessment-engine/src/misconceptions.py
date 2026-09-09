def misconception_probe(question_id, misconception_id, wrong_answer,
                       explanation, correction):
    return {
      "question_id":question_id,
      "misconception_id":misconception_id,
      "wrong_answer":wrong_answer,
      "explanation":explanation,
      "correction":correction
    }
