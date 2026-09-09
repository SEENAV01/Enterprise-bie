import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[1]))

from semantic_retrieval import tfidf_index, search, build_retrieval_ir, validate_retrieval

def test_lexical_retrieval_ranks_matching_section():
    index = tfidf_index({
        "s1":"electric charge positive negative",
        "s2":"photosynthesis plants sunlight",
        "s3":"electric field force charge"
    })
    result = search(index, "electric charge", top_k=2)
    assert result[0]["document_id"] in {"s1","s3"}

def test_retrieval_ir_has_cross_section_links():
    knowledge = {
        "evidence_index":{
            "b1":{"text":"Electric charge is positive or negative."},
            "b2":{"text":"Charge creates an electric field."}
        },
        "claims":[
            {"claim_id":"c1","source_block_id":"b1","text":"Electric charge is positive or negative."},
            {"claim_id":"c2","source_block_id":"b2","text":"Charge creates an electric field."}
        ],
        "entities":[
            {"entity_id":"entity:charge","label":"charge","source_claims":["c1","c2"]}
        ]
    }
    structure = {"tree":[
        {"section_id":"s1","title":"Charge","content_blocks":["b1"],"children":[],"level":1,"start_page":1},
        {"section_id":"s2","title":"Field","content_blocks":["b2"],"children":[],"level":1,"start_page":2}
    ],"flat":[
        {"section_id":"s1","title":"Charge"},
        {"section_id":"s2","title":"Field"}
    ]}
    ir=build_retrieval_ir(knowledge, structure)
    assert len(ir["concept_links"]) == 1
    assert validate_retrieval(ir,knowledge)["passed"] is True
