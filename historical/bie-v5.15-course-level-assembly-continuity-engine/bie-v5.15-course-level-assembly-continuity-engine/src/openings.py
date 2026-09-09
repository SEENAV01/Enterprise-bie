def chapter_opening(chapter_id,template,objective_preview,
                    duration_policy="CONTENT_DRIVEN"):
    return {"chapter_id":chapter_id,"type":"OPENING","template":template,
            "objective_preview":objective_preview,
            "duration_policy":duration_policy}

def chapter_closing(chapter_id,summary_points,next_preview,
                    duration_policy="CONTENT_DRIVEN"):
    return {"chapter_id":chapter_id,"type":"CLOSING",
            "summary_points":summary_points,"next_preview":next_preview,
            "duration_policy":duration_policy}
