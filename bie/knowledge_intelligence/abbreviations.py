class E(ValueError):pass
def register(short,long,anchor,scope="book"):
 s=str(short).strip();l=str(long).strip()
 if not s or not l or not anchor or s.casefold()==l.casefold():raise E("abbreviation")
 return {"short":s,"expansion":l,"anchor_id":anchor,"scope":scope}
