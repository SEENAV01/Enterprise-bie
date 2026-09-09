import hashlib
class E(ValueError):pass
def inspect_pdf(data,page_count):
 if not isinstance(data,(bytes,bytearray)) or not data.startswith(b"%PDF-"):raise E("not pdf")
 if page_count<1:raise E("pages")
 return {"source_hash":hashlib.sha256(data).hexdigest(),"page_count":page_count,"byte_length":len(data)}
