def accessibility_contract(captions=True,transcript=True,
                           keyboard=True,screen_reader=True,
                           reduced_motion=True):
    return {"captions":captions,"transcript":transcript,
            "keyboard":keyboard,"screen_reader":screen_reader,
            "reduced_motion":reduced_motion}
