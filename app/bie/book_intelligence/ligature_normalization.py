class E(ValueError):pass
MAP={"ﬀ":"ff","ﬁ":"fi","ﬂ":"fl","ﬃ":"ffi","ﬄ":"ffl"}
def normalize(text):
 if not isinstance(text,str):raise E("text")
 return "".join(MAP.get(c,c) for c in text)
