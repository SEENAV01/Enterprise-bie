
from pathlib import Path
from pypdf import PdfReader
import hashlib, json

def sha256_file(path):
    h=hashlib.sha256()
    with open(path,"rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()

def extract_pdf(path):
    path=Path(path)
    reader=PdfReader(str(path))
    pages=[]
    for i,page in enumerate(reader.pages,1):
        text=page.extract_text() or ""
        pages.append({"page":i,"text":text})
    return {
      "book_id":path.stem,
      "source":{"filename":path.name,"sha256":sha256_file(path)},
      "pages":pages,
      "page_count":len(pages)
    }

def save_json(obj,path):
    Path(path).write_text(json.dumps(obj,indent=2,ensure_ascii=False))
