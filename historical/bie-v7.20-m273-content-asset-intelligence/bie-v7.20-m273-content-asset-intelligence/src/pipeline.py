from metadata import build_metadata,validate_metadata
from classification import classify_asset,tags_for_asset
from fingerprint import perceptual_fingerprint,near_duplicate
from embedding import embedding_contract,search
from suitability import suitability_score,rank_assets

def build_m273_runtime():
    a=build_metadata("asset-001","image",1920,1080,0,source="render")
    b=build_metadata("asset-002","image",1920,1080,0,source="render")
    meta_ok=validate_metadata(a)
    classification=classify_asset(a)
    tags=tags_for_asset(a)
    fp1=perceptual_fingerprint([a["width"],a["height"],a["media_type"]])
    fp2=perceptual_fingerprint([b["width"],b["height"],b["media_type"]])
    # identical normalized features intentionally demonstrate near-duplicate detection
    duplicate=near_duplicate(fp1,fp2)
    index=[
      embedding_contract("asset-001",[1.0,0.0,0.2],"bie-embed-v1"),
      embedding_contract("asset-002",[0.8,0.1,0.1],"bie-embed-v1")
    ]
    matches=search([1.0,0.0,0.0],index,2)
    requirements={"media_type":"image","min_width":1280,"min_height":720}
    suitability=suitability_score(a,requirements)
    ranking=rank_assets([a,b],requirements)
    return {"schema_version":"7.20","metadata":a,"metadata_validation":meta_ok,
            "classification":classification,"tags":tags,
            "fingerprints":{"asset_001":fp1,"asset_002":fp2,"near_duplicate":duplicate},
            "embedding_index":{"matches":matches},
            "suitability":{"score":suitability,"ranking":ranking},
            "asset_intelligence_gate":{"valid":meta_ok["valid"] and
                                       classification["class"]=="IMAGE" and
                                       duplicate and suitability["score"]>=0.9,
                                       "errors":[]}}
