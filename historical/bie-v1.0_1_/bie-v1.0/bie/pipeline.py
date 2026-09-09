
from pathlib import Path
import json
from .pdf_ingest import extract_pdf
from .stages import m3_extract,m4_frontier,m5_verify,m6_lesson,m7_scene,m8_game

def run_book(pdf_path, out_dir="artifacts"):
    out=Path(out_dir); out.mkdir(parents=True,exist_ok=True)
    book=extract_pdf(pdf_path)
    (out/"m2.json").write_text(json.dumps(book,indent=2,ensure_ascii=False))

    m3=m3_extract.run(book)
    (out/"m3.json").write_text(json.dumps(m3,indent=2,ensure_ascii=False))

    m4=m4_frontier.run(m3)
    (out/"m4.json").write_text(json.dumps(m4,indent=2,ensure_ascii=False))

    m5=m5_verify.run(m4)
    (out/"m5.json").write_text(json.dumps(m5,indent=2,ensure_ascii=False))

    if m5["decision"]=="REVIEW":
        raise RuntimeError("M5 requires review; downstream generation stopped.")

    m6=m6_lesson.run(m4,m5)
    (out/"m6.json").write_text(json.dumps(m6,indent=2,ensure_ascii=False))
    m7=m7_scene.run(m6)
    (out/"m7.json").write_text(json.dumps(m7,indent=2,ensure_ascii=False))
    m8=m8_game.run(m6)
    (out/"m8.json").write_text(json.dumps(m8,indent=2,ensure_ascii=False))
    return {"m2":book,"m3":m3,"m4":m4,"m5":m5,"m6":m6,"m7":m7,"m8":m8}
