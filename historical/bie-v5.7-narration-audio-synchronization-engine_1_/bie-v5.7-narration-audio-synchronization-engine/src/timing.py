def timing_from_words(words, fps=30, words_per_minute=145,
                    pauses=None):
    pauses=pauses or {}
    frames_per_word=fps*60/words_per_minute
    frame=0; timed=[]
    for i,w in enumerate(words):
        start=round(frame)
        frame += frames_per_word
        frame += pauses.get(i,0)*fps
        timed.append({"word_index":i,"word":w,
                      "start_frame":start,"end_frame":round(frame)})
    return timed

def segment_timing(text, start_frame=0, fps=30, words_per_minute=145):
    words=text.split()
    raw=timing_from_words(words,fps,words_per_minute)
    offset=start_frame
    return [{**x,"start_frame":x["start_frame"]+offset,
             "end_frame":x["end_frame"]+offset} for x in raw]
