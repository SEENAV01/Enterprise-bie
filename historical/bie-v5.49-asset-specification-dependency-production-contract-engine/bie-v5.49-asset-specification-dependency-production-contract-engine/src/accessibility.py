def accessibility_requirement(captions=None,alt_text=None,
                                keyboard=None,contrast=None,
                                transcript=None):
    return {"captions":captions,"alt_text":alt_text,
            "keyboard":keyboard,"contrast":contrast,
            "transcript":transcript}
