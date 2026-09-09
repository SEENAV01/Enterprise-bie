import json,sys
from pathlib import Path
from chunking import chunk_document
from long_book import batch_plan

def prepare(document_json:str,out_json:str):
    pages=json.loads(Path(document_json).read_text())
    chunks=chunk_document(pages)
    batches=batch_plan(chunks)
    Path(out_json).write_text(json.dumps({
      "stage":"MODEL_READY_INPUT",
      "chunk_count":len(chunks),
      "batch_count":len(batches),
      "batches":batches
    },indent=2,ensure_ascii=False))
    return chunks,batches

if __name__=="__main__":
    prepare(sys.argv[1],sys.argv[2])
