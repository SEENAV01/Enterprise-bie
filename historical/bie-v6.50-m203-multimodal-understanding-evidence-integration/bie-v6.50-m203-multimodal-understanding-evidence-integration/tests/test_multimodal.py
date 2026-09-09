import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1] / "src"))

from modalities import modality_record, valid
from layout import layout_region, ordered
from evidence import multimodal_evidence, grounded
from cross_modal import cross_modal_link, valid as cross_valid
from figure_table_equation import structured_object, complete
from ocr_layout import extraction, usable
from verification import verification, passed
from provenance import provenance, traceable

def test_modalities_and_layout():
    a = modality_record("a","s","TEXT","text://a",1,confidence=.9)
    b = modality_record("b","s","IMAGE","image://b",1,confidence=.9)
    assert valid(a) and valid(b)
    regions = ordered([
        layout_region("r2","s",2,"TEXT",[0,0,1,1],2),
        layout_region("r1","s",1,"TEXT",[0,0,1,1],1)
    ])
    assert [r["region_id"] for r in regions] == ["r1","r2"]

def test_multimodal_evidence():
    e = multimodal_evidence("e","s",["a","b"],"joint claim")
    link = cross_modal_link("l","s",["a","b"],"EXPLAINS")
    obj = structured_object("o","s","FIGURE",["b"],"diagram")
    ocr = extraction("x","s",1,"some text",True,True,.9)
    p = provenance("e",["s"],["a","b"],["e"],"extract")
    v = verification("v","e","PASS",["e"])
    assert grounded(e) and cross_valid(link)
    assert complete(obj) and usable(ocr)
    assert traceable(p) and passed(v)
