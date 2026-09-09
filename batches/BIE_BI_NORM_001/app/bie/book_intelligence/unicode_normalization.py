import unicodedata
class E(ValueError):pass
def normalize(text,form="NFC"):
 if not isinstance(text,str):raise E("text")
 if form not in {"NFC","NFKC"}:raise E("form")
 return unicodedata.normalize(form,text)
