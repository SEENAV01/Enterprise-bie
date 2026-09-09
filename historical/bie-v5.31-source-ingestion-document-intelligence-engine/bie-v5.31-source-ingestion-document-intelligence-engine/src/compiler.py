from document import document
from canonical import canonical_source
from ocr import ocr_gate
from tables import validate_table
from formulas import formula_gate

def compile_source(document_id,source_uri,media_type,pages,regions,blocks,
                   tables=None,figures=None,formulas=None,
                   ocr_results=None):
    doc=document(document_id,source_uri,media_type)
    ocr_checks=[ocr_gate(x) for x in (ocr_results or [])]
    table_checks=[validate_table(x) for x in (tables or [])]
    formula_checks=[formula_gate(x) for x in (formulas or [])]
    errors=[]
    if any(not x["valid"] for x in ocr_checks): errors.append("OCR_REVIEW_REQUIRED")
    if any(not x["valid"] for x in table_checks): errors.append("TABLE_STRUCTURE_INVALID")
    if any(not x["valid"] for x in formula_checks): errors.append("FORMULA_REVIEW_REQUIRED")
    return {"source":canonical_source(doc,pages,regions,blocks,tables,figures,formulas),
            "extraction_qa":{"ocr":ocr_checks,"tables":table_checks,
                             "formulas":formula_checks},
            "quality_gate":{"valid":not errors,"errors":errors}}
