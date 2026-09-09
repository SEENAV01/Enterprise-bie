from modalities import modality_record, valid as modality_valid
from layout import layout_region, ordered
from evidence import multimodal_evidence, grounded
from cross_modal import cross_modal_link, valid as cross_valid
from figure_table_equation import structured_object, complete
from ocr_layout import extraction, usable
from verification import verification, passed
from provenance import provenance, traceable

def build_multimodal_understanding():
    source_id = "book-1"

    regions = ordered([
        layout_region("region-2", source_id, 1, "FIGURE",
                      [0, 300, 600, 700], 2),
        layout_region("region-1", source_id, 1, "TEXT",
                      [0, 0, 900, 280], 1)
    ])

    text = modality_record(
        "record-text-1", source_id, "TEXT",
        "text://page/1/region/1", 1,
        regions[0]["bbox"], 0.99
    )
    figure = modality_record(
        "record-figure-1", source_id, "IMAGE",
        "image://page/1/figure/1", 1,
        regions[1]["bbox"], 0.96
    )

    ocr = extraction(
        "ocr-1", source_id, 1,
        "Charge is a conserved physical property.",
        ocr=True, layout_aware=True, confidence=0.98
    )

    fig = structured_object(
        "figure-1", source_id, "FIGURE",
        ["record-figure-1"], "electric charge diagram"
    )

    evidence = multimodal_evidence(
        "evidence-1", source_id,
        ["record-text-1", "record-figure-1"],
        "The text and figure jointly explain electric charge.",
        0.95
    )

    link = cross_modal_link(
        "link-1", source_id,
        ["record-text-1", "record-figure-1"],
        "EXPLAINS"
    )

    prov = provenance(
        "evidence-1", [source_id],
        ["record-text-1", "record-figure-1"],
        ["evidence-1"], "layout-aware multimodal extraction"
    )

    check = verification(
        "check-1", "evidence-1", "PASS",
        ["evidence-1"]
    )

    return {
        "schema_version": "6.50",
        "source_id": source_id,
        "regions": regions,
        "modalities": [text, figure],
        "ocr_extraction": ocr,
        "structured_object": fig,
        "evidence": evidence,
        "cross_modal_link": link,
        "provenance": prov,
        "verification": check,
        "quality_gate": {
            "valid": (
                all(modality_valid(x) for x in [text, figure])
                and usable(ocr)
                and complete(fig)
                and grounded(evidence)
                and cross_valid(link)
                and traceable(prov)
                and passed(check)
            ),
            "errors": []
        }
    }
