def speech_plan(voice_id,language,rate=1.0,pitch=None,
                pronunciation_lexicon=None):
    return {"voice_id":voice_id,"language":language,"rate":rate,
            "pitch":pitch,"pronunciation_lexicon":
            pronunciation_lexicon or {}}

def speech_estimate(text,words_per_second=2.5):
    words=len(text.split())
    return words/words_per_second if words else 0.0
