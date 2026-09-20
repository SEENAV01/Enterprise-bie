# My Book Intelligence Engine — canonical enterprise workspace

This is a continuation of the existing BIE architecture, not a replacement project.

The post-DIR adoption adds the supplied VIS, ANI, DSL and COMP source through
`BIE-COMP-H12-001`. Production code lives in `bie/`. Original supplied packages,
including intermediate batches and Master Backups, remain immutable evidence.
`app/bie` is a compatibility layer, never a second production implementation.

## Run the source/integrity gates

```sh
python -B scripts/integrated_check.py --output-dir /tmp/bie-verification
python -B scripts/verify_post_dir.py --output /tmp/bie-verification/post-dir.json
```

The compiler's test workers require the pinned Python packages in
`requirements-comp-h3.txt`, Node/TypeScript and FFmpeg/ffprobe. The canonical CI
workflow installs its explicitly pinned test-tool profile. That profile is NOT
the full generated Remotion project runtime and must not be advertised as one.

## Source and history

- `bie/visual_intelligence`: the supplied final VIS overlay, including governed rebuilt REP.
- `bie/animation_intelligence`: the supplied ANI H4 implementation.
- `bie/scene_ir`: final DSL with the two documented COMP-owned element amendments.
- `bie/compiler`: the implemented compiler; `bie/video_compiler` is an older reserved namespace.
- `backups/ingested/post_dir_inputs`: every supplied section-labelled artifact plus both supplied integration-instruction files, unchanged.
- `manifests/post_dir_supplied_inputs.json`: 386 supplied filenames and their exact hashes.
- `manifests/post_dir_integration_004.json`: archive/member accounting, source adoption, collisions and explicit canonical path adaptations.

Ten original VIS LAYOUT atomic ZIP hashes are referenced but those individual ZIP
bytes were not supplied. Their combined source is available and integrated. This
absence is recorded rather than filled with recreated archives. Preservation of
all supplied inputs does not imply that every historical delivery ever made is available.

## Product direction and acceptance boundary

BIE must autonomously understand a book, derive concepts/prerequisites/reasoning,
choose pedagogy, direct a lesson, plan meaningful visuals and animation, compile
and render actual animated and real-footage teaching, and support revision games.
Source files or validated supplied plans are not substitutes for those capabilities.
No generic slide-template or direct raw-book-to-Remotion shortcut is introduced here.

This adoption verifies source/provenance and technical integration contracts.
Real pinned Remotion compilation, actual rendering, trusted frame/audio inspection,
real-book end-to-end teaching quality, the downstream AUDIO/game work and final
enterprise acceptance remain open. No finished application or cinematic-quality
video is claimed merely because the repository and component tests pass.

See `docs/bie/CURRENT_STATE.md` and `task_registry/continuation.json`.
