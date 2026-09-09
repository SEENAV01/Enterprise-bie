class E(ValueError):pass
MAP={"−":"-","–":"-","—":"-","×":"×","÷":"÷","µ":"μ"}
def normalize(text):
 if not isinstance(text,str):raise E("text")
 return "".join(MAP.get(c,c) for c in text)
