def equation_sequence(equation,steps):
    return {
      "equation":equation,
      "events":[
        {"step":i+1,"text":s,"reveal":"AFTER_NARRATION_CUE"}
        for i,s in enumerate(steps)
      ]
    }
