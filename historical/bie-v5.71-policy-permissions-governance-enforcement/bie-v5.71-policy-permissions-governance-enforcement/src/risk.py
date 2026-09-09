def risk_classification(action):
    high={"DELETE_PRODUCTION","CHANGE_GLOBAL_POLICY",
          "MODIFY_LEARNER_STATE","RELEASE_PRODUCTION"}
    if action in high: return "HIGH"
    if action in {"GENERATE_CONTENT","RENDER","VALIDATE"}: return "MEDIUM"
    return "LOW"
