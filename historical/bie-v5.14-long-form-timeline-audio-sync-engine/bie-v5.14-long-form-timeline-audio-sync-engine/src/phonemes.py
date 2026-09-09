def phoneme_event(symbol,start_frame,end_frame):
    return {"symbol":symbol,"start_frame":start_frame,"end_frame":end_frame}

def align_word(word,start_frame,end_frame,phonemes=None):
    return {"word":word,"start_frame":start_frame,"end_frame":end_frame,
            "phonemes":phonemes or []}
