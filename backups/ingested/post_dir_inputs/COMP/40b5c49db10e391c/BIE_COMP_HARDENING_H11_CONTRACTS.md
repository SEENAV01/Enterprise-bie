# COMP H11: verified visual-media contracts

This is a bounded continuation of H10, not a replacement compiler or a section-exit audit. The changes address original media/asset handoff and existing R01/R02 behavior findings. All actual-render, downstream instructional and real-book gates remain open.

## Source, bundle, bytes, then presentation

The original `bundle_assets` receipt feeds `bind_visual_bundle`. The latter reads the actual locally bundled bytes, checks their content hashes, runs bounded decoders and adds `metadata.compiler_media_v1` to a copied Scene. It never trusts the receipt's `passed` field alone, never downloads media, never changes the original object and never claims that a supplied rights reference establishes permission. `scripts/bind_visual_assets.py` exposes the handoff.

Every adopted image/video element is bound to a manifest asset ID, content-addressed public path, byte length, SHA256, verified metadata and its existing source/reasoning/rights references. Conflicts, unused assets and unsupported properties are rejected. Paths cannot traverse directories or resolve through symlinks; file descriptors require regular bounded files. Missing or altered bytes fail before publication and again during render revalidation. Narration assets and visual assets share the established private staging/publication path without replacing one another.

The image decoder actually loads the pixels in the existing H7 kernel-isolated no-proc worker. Static PNG, JPEG and WebP are supported; animated images and nonidentity EXIF orientations require explicit upstream normalization. Limits: 16 million pixels, 64 MiB per file, 256 MiB per manifest and 64 asset entries. The video decoder is actual isolated ffprobe: one H.264 yuv420p video stream, square pixels, no rotation, zero-origin constant-frame-rate timestamps and verified frame count/duration; optionally one AAC mono/stereo audio stream. Other profiles fail closed. No browser-worker isolation waiver is added.

## Image rendering

A crop is `[x, y, width, height]` with explicit `normalized-xywh` or `source-pixels-xywh` units. The original image builder now records units when it creates a crop; its no-crop behavior is unchanged. Verified cropped source rectangles are fitted with aspect-preserving contain geometry. The full original media bytes remain unchanged; generated CanvasImage geometry and a bounded clipping viewport realize the crop. Alternative text is retained. Native resampling can blend pixels along fractional raster boundaries: this is not a promise of nearest-neighbor/exact-pixel boundary reproduction. There is no implicit focus crop, stretch, source-byte rewriting or unsupported CSS property suppression.

## Video timeline

The source `trim_start_ms`, exclusive `trim_end_ms`, and optional `timeline_start_ms` must map exactly to composition frames. No implicit millisecond rounding occurs. A missing trim end uses verified source duration only when frame aligned. The finite clip must fit within both the verified source and scene. Remotion `Sequence` defines the display interval and `Video` receives `trimBefore`/`trimAfter` in composition-frame units. The plan and layout use the same interval. Outside it the layer owner is hidden; inside it direct and reverse seeking derive the same source clock. CFR sample oracle: floor((local-frame + trim-before) * source-fps / composition-fps). Runtime compatibility with actual pinned Remotion remains unverified.

`@remotion/media` is included at the unchanged target Remotion pin, not at an ungoverned/latest version. Source audio policy must explicitly be `preserve` or `muted`; muting requires a bound reasoning reference. This batch does not verify sound playback. An unresolved external `captions_ref` is blocked rather than silently treated as visible captions; captions must be resolved through the existing H6 source-bound timeline. Embedded audible video plus separate narration requires an explicitly verified mix and is blocked by the present bounded contract. No TTS, transcript correctness, AV teaching synchronization or arbitrary codec support is claimed.

## Adopted execution paths

`compile_h3_scene`, source publication, `require_h3_workspace`, the existing checked CLI and bounded layout-repair loop adopt the asset contract. A crop/trim source gate does not itself prove the bytes exist; publication and revalidation add the byte checks. The repair loop receives verified visual bytes while preserving fixed media and existing supported repair owners. This is not autonomous image redesign/cropping or a new universal repair owner. Existing standalone unbound emitters remain legacy diagnostic APIs, not accepted production paths; crop/trim intent can no longer silently disappear there.

## Technical validation boundaries

The diagnostic media bridge transpiles the real generated TypeScript, with explicitly labelled React/Remotion API doubles. It creates native image/video elements in real Chromium. Only exact in-memory verified assets are allowed through the route handler; external requests are blocked. Diagnostic video is muted, waits for native decode/seek and records its time/size. The native canvas is CORS-enabled for only those verified routes, not unrestricted network access. These source/body measurements do not mint an actual-render witness.

Five fixed cases exercise full image, cropped image, trimmed video, video with state and combined image/video. Every local frame is measured; forward/reverse TS tests independently check the schedule. Four predeclared pixels per active video frame are compared to an independently FFmpeg-decoded fixture reference. Tolerance is at most 5 in any 8-bit RGB channel, and at most 1e-6 seconds of seek error. This sparse reference tests this fixture's frame clock, not full-image semantic quality, general colorspace equivalence or actual Remotion rendering.

## Dependencies and documentation

Existing Python pins in `requirements-comp-raster.txt`, H7 Linux worker prerequisites, installed Node/TypeScript, FFmpeg/ffprobe and Chromium are required. Full generated projects retain Remotion 4.0.506 and TypeScript 5.9.3. Diagnostics use the actual locally installed TypeScript 5.8.3; no compatibility with the complete pinned dependency tree is inferred from those diagnostics.

Official API references checked September 19, 2026:
- https://www.remotion.dev/docs/media/video (trim units, error policy, fit and mute)
- https://www.remotion.dev/docs/sequence (local time and finite lifetime)
- https://www.remotion.dev/docs/use-current-frame (frame evaluation)

No external fonts or font files are distributed. Source hashes and receipts are integrity records, not cryptographic signatures from an independent authority.
