def preview_job(composition_id,start_frame=0,
                duration_frames=150,scale=0.5):
    return {"composition_id":composition_id,"start_frame":start_frame,
            "duration_frames":duration_frames,"scale":scale,
            "status":"QUEUED"}
