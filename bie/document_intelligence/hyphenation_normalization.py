import re
class E(ValueError):pass
def repair(text):
 if not isinstance(text,str):raise E("text")
 return re.sub(r"([A-Za-z]{2,})-\s*\n\s*([a-z]{2,})",r"\1\2",text)
