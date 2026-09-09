def render_contract():
    return {
      "resolution":"1920x1080",
      "fps":30,
      "timing":"AUDIO_AUTHORITATIVE",
      "render_strategy":"INCREMENTAL",
      "qa_required_before_publish":True,
      "failed_scene_policy":"REPAIR_THEN_RERENDER",
      "final_publish_requires":"COURSE_QA_PASS"
    }
