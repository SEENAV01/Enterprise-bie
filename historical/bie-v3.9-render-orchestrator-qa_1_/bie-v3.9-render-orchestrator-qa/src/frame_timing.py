def seconds_to_frames(seconds, fps):
    if seconds < 0 or fps <= 0:
        raise ValueError("INVALID_TIMING")
    return int(round(seconds * fps))

def scene_duration_frames(audio_start, audio_end, fps, padding_frames=0):
    return seconds_to_frames(max(0,audio_end-audio_start),fps)+padding_frames
