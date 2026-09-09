def mix_profile(master_lufs=-14.0, narration_db=0.0,
                music_db=-18.0, sfx_db=-12.0, duck_music_db=-8.0):
    return {"master_lufs":master_lufs,"narration_db":narration_db,
            "music_db":music_db,"sfx_db":sfx_db,
            "duck_music_db":duck_music_db}

def valid(profile):
    return isinstance(profile["master_lufs"],(int,float))
