import re
class E(ValueError):pass
def extract(text):
 if not isinstance(text,str):raise E("text")
 nums=[int(x) for x in re.findall(r"\[(\d+)\]",text)]
 author_year=[(a,int(y)) for a,y in re.findall(r"\(([A-Z][A-Za-z-]+),\s*(\d{4})\)",text)]
 return {"numeric":tuple(nums),"author_year":tuple(author_year)}
