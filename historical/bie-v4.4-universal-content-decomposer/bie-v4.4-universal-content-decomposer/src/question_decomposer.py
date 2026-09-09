import re

PATTERNS={
"WHAT":[r"\bwhat\b",r"\bdefine\b",r"\bmeaning\b"],
"WHY":[r"\bwhy\b",r"\bcause\b",r"\breason\b"],
"HOW":[r"\bhow\b",r"\bsteps?\b",r"\bprocess\b",r"\bmethod\b"],
"WHEN":[r"\bwhen\b",r"\btime\b",r"\bperiod\b"],
"WHERE":[r"\bwhere\b",r"\blocation\b",r"\bplace\b"],
"WHO":[r"\bwho\b",r"\bperson\b",r"\bscientist\b"]
}

def detect_question_dimension(text):
    low=text.lower()
    hits=[]
    for dim,patterns in PATTERNS.items():
        if any(re.search(p,low) for p in patterns):
            hits.append(dim)
    return hits

def decompose_question(text):
    dims=detect_question_dimension(text)
    return [{"dimension":d,"text":text} for d in dims]
