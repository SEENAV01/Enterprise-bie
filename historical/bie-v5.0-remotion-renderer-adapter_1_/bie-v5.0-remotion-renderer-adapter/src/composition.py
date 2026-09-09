def composition_metadata(spec,composition_id="BookLesson"):
    return {
      "id":composition_id,
      "fps":spec["fps"],
      "width":1920,
      "height":1080,
      "durationInFrames":spec["duration_frames"],
      "defaultCodec":"h264",
      "pixelFormat":"yuv420p"
    }
