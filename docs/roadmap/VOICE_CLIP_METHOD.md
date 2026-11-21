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

## Measuring the voice on the VM's CPU (₹0): the "voice" job

A VM job with `"section": "voice"` (`tools/vm_voice.py speak`, `tools/vm_voice_worker.py`) speaks the first sentences
of one video's narration with Chatterbox Multilingual (Hindi) on the machine's own CPU:

- `"reference": "default"` uses Chatterbox's built-in voice, so the speed can be measured before Navin's clip arrives;
  `"reference": "navin"` uses his clip from `/etc/bie/voice/` with pitch −2 semitones (agreement of 3 November).
- The first job makes a separate voice environment on the machine (`/var/lib/bie/voice-venv`, pinned: torch and
  torchaudio 2.6.0 CPU builds, chatterbox-tts 0.1.7, av 18.0.0, setuptools 80.9.0 for the watermarker; the model `ResembleAI/chatterbox` at a fixed
  revision). Licences: MIT (Chatterbox and its model), BSD-3 (torch, PyAV), Apache/MIT/BSD/ISC for the rest; nothing
  of it goes into `apps/`.
- The audio goes only to `/var/lib/bie/private/voice/<job id>/` (mode 700). The public run folder gets numbers only:
  seconds of audio and of CPU per sentence, the real-time factor, an estimate for the whole video, and
  `durations.json` (sentence → seconds, the shape the scene-plan timeline takes for real voice durations).
- Chatterbox marks its audio with its own inaudible watermark (Perth), which says the audio is generated.

## Measured on the VM's CPU (20 November 2026)

VM job `p1v-voice-measure-v4b` (₹0; results `blindtest-results:runs/vm-p1v-voice-measure-v4b-brain-voice/`, numbers
only): Chatterbox Multilingual's built-in voice spoke the first 8 sentences of Money v4 in Hindi on the Hostinger KVM 2
(2 CPUs, 7.8 GB RAM).

| Measure | Value |
| --- | --- |
| Sentences made | 8 of 8 (35.9 s of audio) |
| CPU time | 349.8 s, real-time factor **9.7** (each second of voice takes about 10 s of CPU) |
| Model load | 56.8 s (once per job); voice environment build 83 s (once) |
| Peak RAM | 6.4 GB of 7.8 GB |
| Whole Money v4 (8,284 characters) | about 12.3 min of voice, about **2 hours** of CPU |

So on this CPU one video's voice takes about 2 hours and a 12-video chapter about a day; it works for a sample or one
chapter overnight, not for whole books. The first run (`p1v-voice-measure-v4`) stopped at load on a missing
`pkg_resources` (the watermarker's); the voice environment now pins setuptools (PR #159). Not yet judged: how the
Hinglish sounds (English words in Roman, Hindi pronunciation) — the audio stays on the VM, and a listening check (or the
STT check per sentence) comes with Navin's clip.

## Still open (Navin's decisions)

1. **Speed and money:** the CPU measure above comes first (₹0); a GPU (free quota or hourly rental) only if the CPU is
   too slow, and only on his budget yes.
2. **Google Drive access** for the voiced videos (above).

Until the clip is on the VM and the voice is measured, every video stays captions-only.

## 21 November 2026: Navin's recording, Kokoro + OpenVoice, and autodub

Navin's cards (21 November 2026):

- **How his voice is made:** "Seedha Kokoro + OpenVoice". The base voice is a free engine (Kokoro for Hindi/Hinglish and
  English; AI4Bharat Indic-TTS for Tamil, Telugu, Malayalam and Marathi) and OpenVoice V2's tone-colour converter (MyShell,
  MIT) turns it into his timbre. Chatterbox stays measured but unused (about 2 hours of CPU per video).
- **How the recording reaches BIE:** "Is chat mein bhej doon". He sent a 5 min 18 s reading of the Q14 script in the
  planning chat. It is kept only in Claude's private cloud workspace (folder mode 700, file mode 600), never in the
  repository, a run folder, GitHub Actions or a review page. This replaces the "VM only" rule of 5 November for this one
  recording, by his choice on the card (the card said so). Voice made from it reaches him only as files in the private
  chat. Production on the VM needs his tone file there too: a separate decision for him.
- **Autodub languages:** Tamil, Telugu, Malayalam, Marathi and English (his answer, typed).
- **His words about the recording:** "bahut galtiyan hai us voice mein par clone krne ke liye kaam mein laa sakte ho ...
  bolne ka niyam isse mat lena, isko polish karna hai voice ke taur par bhi aur teacher ki tarah kahan pause kaisa tone".
  So only his timbre is taken from it. How a line is said is BIE's teacher rule (`bie/brain/studio_voice.py`: a question
  on its own with 0.45 s after it and said a little slower; a short breath at ";", ":" and "—"; the rest in one flow).

What the recording holds (measured by code, numbers only): 318 s; Whisper (large-v3-turbo, MIT) heard 510 words, 96
words a minute, speech 81% of the time, 24 pauses over 0.8 s (the longest 9.2 s), one word said twice, 6 unsure words;
noise floor about −72 dB, one clipped sample. 32 clean stretches (3–10 s, no gap over 0.45 s, no restart, every word heard
clearly) total 227 s; only these make his tone colour.

### Second round, 21 November 2026: "voice artificial hai", and Chatterbox's conversion

Navin heard the first sample (OpenVoice, likeness 0.875): "aawaj ko sur sudhaarna hai; meri recording se lehja to dekh
sakte ho, jahan prashan hai wahan kaise prashan ka utaar ... jisse cheejen ek continuous paragraph jaisi na lage; voice
ko thoda human touch do, saaf lag raha hai voice artificial hai". So his lehja may now be learned from the recording; his
slips still may not.

Measured on his reading: on a question word his pitch rises about 8 semitones above his middle and the question's end
falls about 2; statements end about half a semitone low. The base voice already rose 6 to 9 semitones on question words,
so a code reshaping of its pitch (WORLD, pyworld MIT) changed little. What changes the feel is the voice itself:

| Way (same 4 Q14 lines) | Likeness to his reading | CPU per second of voice (2 CPUs) |
| --- | --- | --- |
| Chatterbox speaking, lehja and timbre from a 12 s clean question-and-answer clip of his | 0.96 | about 8 |
| Kokoro speaking, Chatterbox's voice conversion (S3Gen) into his voice | 0.94 | about 4.5 |
| Kokoro, slower, with his question shape, OpenVoice | 0.87 | about 1.6 |
| His own reading, half against half (the ceiling) | 0.97 | |

Chatterbox speaking once added two words that were not in the line; made part by part with a Whisper check, all six
parts came out clean. Tamil (Indic-TTS male, a test sentence) through Chatterbox's conversion: likeness 0.71 → 0.91,
Whisper heard 82% of the words (97% before conversion), so a Tamil speaker should listen once.

His card: **"6: Kokoro + Chatterbox badlaav"**, and Claude chooses the clip of his reading that sets the voice. Built:
the voice worker's convert request (`tools/vm_voice_worker.py`, the pinned Chatterbox model) and
`tools/studio_revoice.py --narrator navin --converter chatterbox` (every line said by the base voice, all lines turned
into his voice in one batch in the voice environment, the page built again). OpenVoice stays as the faster way.
