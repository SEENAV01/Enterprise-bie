from segmenter import segment_book
from content_classifier import classify_segment
from decomposition_validator import validate_extractions

def decompose_book(book, candidate_map):
    segments=segment_book(book)
    all_items=[]
    for s in segments:
        all_items.extend(classify_segment(s,candidate_map.get(s["segment_id"],[])))
    validation=validate_extractions(all_items)
    return {
      "schema_version":"4.4",
      "segments":segments,
      "extractions":all_items,
      "validation":validation,
      "policy":{
        "full_text_preserved":True,
        "source_span_required":True,
        "multi_dimension_allowed":True,
        "no_concept_only_reduction":True
      }
    }
