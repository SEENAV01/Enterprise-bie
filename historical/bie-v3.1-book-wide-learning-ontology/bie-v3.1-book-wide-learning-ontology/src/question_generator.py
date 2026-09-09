TEMPLATES={
"what":["What is {topic}?","What are the main properties of {topic}?","What components make up {topic}?"],
"who":["Who is associated with {topic}?","Who/what is affected by {topic}?"],
"when":["When does {topic} occur?","When did {topic} develop or change?"],
"where":["Where does {topic} occur or apply?","Where is {topic} located?"],
"why":["Why does {topic} happen?","Why is {topic} important?","What causes {topic}?"],
"how":["How does {topic} work?","How is {topic} derived or performed?","What are the steps in {topic}?"],
"which":["Which conditions or categories apply to {topic}?","How does {topic} compare with alternatives?"],
"how_much":["How much/how many is relevant to {topic}?","How is {topic} measured?"]
}

def generate_questions(topic,axes=None):
    axes=axes or list(TEMPLATES)
    return [{"axis":a,"question":q.format(topic=topic)} for a in axes for q in TEMPLATES[a]]
