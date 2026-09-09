def map_applications(topic, applications):
    return [{
      "topic":topic,
      "application":a.get("name"),
      "context":a.get("context"),
      "mechanism_link":a.get("mechanism"),
      "evidence_ids":a.get("evidence_ids",[]),
      "scope":a.get("scope","BOOK")
    } for a in applications]

def classify_application(app):
    return "DAILY_LIFE" if "daily" in app.get("context","").lower() else "CURRENT_WORLD"
