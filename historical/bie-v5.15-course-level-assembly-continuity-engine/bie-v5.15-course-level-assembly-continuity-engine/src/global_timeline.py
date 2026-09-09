def assign_offsets(lessons,lesson_durations):
    offset=0; out=[]
    for l in sorted(lessons,key=lambda x:x.get("order",0)):
        dur=lesson_durations.get(l["lesson_id"],0)
        out.append({**l,"timeline":{"start_frame":offset,"end_frame":offset+dur,
                                     "duration_frames":dur}})
        offset+=dur
    return out,offset
