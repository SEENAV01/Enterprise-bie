def render_policy():
    return {
      "preflight_validation_required":True,
      "missing_assets_block_render":True,
      "audio_video_duration_consistency_checked":True,
      "frame_count_is_deterministic":True,
      "render_fingerprints_enable_caching":True,
      "transient_failures_can_retry":True,
      "preview_is_supported":True,
      "final_output_requires_qa_pass":True,
      "failed_outputs_are_not_release_ready":True
    }
