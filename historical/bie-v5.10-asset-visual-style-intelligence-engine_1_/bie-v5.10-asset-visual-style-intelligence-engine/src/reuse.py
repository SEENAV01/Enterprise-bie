def choose_asset(asset_library, asset_type, semantic_role):
    matches=[a for a in asset_library
             if a.get("asset_type")==asset_type and
                a.get("semantic_role")==semantic_role]
    return sorted(matches,key=lambda x:x.get("version","0"),reverse=True)

def reuse_policy():
    return {
      "prefer_existing_semantic_asset":True,
      "create_new_asset_only_when_no_suitable_match":True,
      "preserve_asset_identity_across_lessons":True,
      "version_assets_instead_of_silent_replacement":True
    }
