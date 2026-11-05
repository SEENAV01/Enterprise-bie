# Navin's voice clip: the private method (5 November 2026)

Navin's answer (decision card, 5 November 2026): **"Haan, sirf VM par private."** His reference clip may be stored, on
his VM only, never in the public repository. This page is the method, shown to him before anything is built.

## What is kept, where

- **The clip:** one file on the VM, `/etc/bie/voice/navin_ref.wav` (folder mode 700, file mode 600, owner the `bie`
  user that runs the jobs). Nothing else holds a copy made by BIE.
- **Never:** the public repository (no branch, not `blindtest-results`, not `codex-jobs`, not even encrypted), GitHub
  Actions (no secret, no artifact, no log line), chat transcripts written to the repo, review pages.
- **Generated voice is treated the same** (agreement of 3 November, section 6): the narration audio made from the clip
  and any video that carries it stay private too. So a video with his voice is rendered and kept on the VM, not
  published to `blindtest-results` like the captions-only review copies are today.

## How it is used

- The voice job runs on the VM (the same job runner as the scene plans): it reads the clip, makes the narration audio
  with the clone voice (Chatterbox Multilingual, pitch −2 semitones, the agreed interim voice), times the words, and
  hands the word times to the scene plan (the cue words already wait for real durations).
- The job writes only timings and durations (numbers, no audio) to the public run folder, so plans and renders can
  line up with the voice without the voice leaving the VM.

## How it can be removed

- Deleting `/etc/bie/voice/` removes the clip and every audio made from it on the VM; nothing to chase elsewhere,
  because nothing was copied out.

## Still open (Navin's decisions)

1. **How the clip reaches the VM** (he works from a tablet): copy it in through the Hostinger panel's terminal or file
   access, or a one-time private upload page on the VM that switches itself off after one file.
2. **Where he watches voiced videos:** a private page served by the VM (password), or another private place he names.
3. **Speed and money:** first measure the clone voice on the VM's own CPU (₹0); a GPU (free quota or hourly rental)
   only if the CPU is too slow, and only on his budget yes.

Until these are settled, every video stays captions-only.
