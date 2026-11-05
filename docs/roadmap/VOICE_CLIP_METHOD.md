# Navin's voice clip: the private method (5 November 2026)

Navin's answer (decision card, 5 November 2026): **"Haan, sirf VM par private."** His reference clip may be stored, on
his VM only, never in the public repository. This page is the method, shown to him before anything is built.

## What is kept, where

- **The clip:** one file on the VM, `/etc/bie/voice/navin_ref.<ext>` (the format his tablet gives: m4a, mp3, wav, ogg,
  webm or flac; folder mode 700, file mode 600, owner the `bie` user that runs the jobs). Nothing else holds a copy made
  by BIE.
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

## How the clip reaches the VM: the one-time upload page (built 5 November 2026)

Navin's answer: **"Ek-baar ka upload page"**. Built as `tools/vm_voice.py upload`, started by
`deployment/codex-vm/bie-voice-upload`. Nothing is switched on by Claude: Navin starts it himself, when he is ready,
from the Hostinger browser terminal (hPanel → VPS → Browser terminal), with one line:

    sudo bash /var/lib/bie/repo/deployment/codex-vm/bie-voice-upload

- The terminal prints a secret link, `https://<VM address>:8443/<secret>`. The secret (32 random characters, new on
  every run) is the page's password: it is shown only in his terminal, never written to a log, a file or GitHub. Every
  other address on that port answers a bare 404.
- He opens the link on his tablet. The browser warns once that the connection is "not private", because the
  certificate was made by the VM itself for this one run (no outside company signs it); the data is still encrypted on
  the way. He taps Advanced → Proceed (Chrome) or Show details → visit (Safari).
- The page takes one audio file (m4a, mp3, wav, ogg, webm or flac; at most 25 MB; checked by its first bytes, not its
  name), stores it as `/etc/bie/voice/navin_ref.<ext>` (mode 600) and closes. It also closes after 20 minutes, or on
  Ctrl+C. It never replaces a clip that is already there unless the line ends with `--replace`.
- If the VM's firewall (ufw) is on, port 8443 is opened only while the page runs and closed again after.
- The page loads nothing from outside (no fonts, scripts or images from other sites) and the machine sends the clip
  nowhere.

What it looks like (a phone-width screenshot of the real page, run locally with a test file) is on the review page
shown to Navin before he switches it on.

## Where voiced videos are watched

Navin's answer: **his Google Drive** (a private folder he names). The access the VM needs to put a file there is a
security decision and is set up with him first; until then voiced videos stay on the VM and nothing with his voice is
published.

## Still open (Navin's decisions)

1. **Speed and money:** first measure the clone voice on the VM's own CPU (₹0); a GPU (free quota or hourly rental)
   only if the CPU is too slow, and only on his budget yes.
2. **Google Drive access** for the voiced videos (above).

Until the clip is on the VM and the voice is measured, every video stays captions-only.
