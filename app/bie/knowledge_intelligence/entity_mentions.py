class E(ValueError):pass
def mention(i,text,anchor,start,end):
 if not i or not text or not anchor or not (0<=start<end<=len(text)):raise E("mention")
 return {"entity_id":i,"anchor_id":anchor,"span":(start,end),"surface":text[start:end]}
