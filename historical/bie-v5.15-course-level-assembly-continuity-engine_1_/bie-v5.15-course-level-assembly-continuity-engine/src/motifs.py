def recurring_motif(motif_id,name,semantic_role,appearances=None):
    return {"motif_id":motif_id,"name":name,"semantic_role":semantic_role,
            "appearances":appearances or []}

def register_appearance(motif,lesson_id,scene_id,usage):
    motif["appearances"].append({"lesson_id":lesson_id,"scene_id":scene_id,
                                 "usage":usage})
    return motif
