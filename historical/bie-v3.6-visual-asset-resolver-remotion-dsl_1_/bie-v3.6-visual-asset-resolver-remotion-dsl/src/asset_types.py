ASSET_SOURCES=[
"BOOK_EXTRACTED","BOOK_RECONSTRUCTED","LIBRARY_REUSABLE",
"VECTOR_GENERATED","REMOTION_NATIVE","EXTERNAL_GENERATED"
]
RISK_LEVELS=["LOW","MEDIUM","HIGH"]

def asset_requirement(asset_id, role, source_preference=None):
    return {
      "asset_id":asset_id,
      "role":role,
      "source_preference":source_preference or [],
      "selected_source":None,
      "fallbacks":[],
      "evidence_ids":[],
      "license_status":"UNKNOWN"
    }
