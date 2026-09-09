COMPONENTS={
"TEXT":"KnowledgeText",
"EQUATION":"Equation",
"SHAPE":"Shape",
"ARROW":"Arrow",
"ICON":"Icon",
"DIAGRAM":"Diagram",
"CHART":"Chart",
"PARTICLE":"ParticleSystem",
"PATH":"Path",
"GROUP":"Group",
"IMAGE":"Image",
"LABEL":"Label",
"HIGHLIGHT":"Highlight",
"MASK":"Mask"
}

def resolve_component(kind):
    return COMPONENTS.get(kind,"KnowledgeText")
