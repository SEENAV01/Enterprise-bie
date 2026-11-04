# Teaching cards (batch 3b, 4 Nov 2026): what the reference videos teach BIE's other sections

The canvas cards (`cards3/<ID>.json`) say how each idea was SHOWN. A teaching card says how it was TAUGHT and how the
teaching and the showing fit together, plus what the video offers BIE's book-understanding, voice, checks, game and
notes sections. Navin's agreement (section 8): the videos teach every section of BIE, not only showing.

Write in English, in our own words. Hindi/Hinglish is fine inside `q` (notes questions) and short quoted terms. Never
copy long passages of the narration; summarise. Facts in the videos may be wrong: describe the teaching, do not
certify the facts.

One JSON file per video: `teach/<ID>.json`

```json
{
  "id": "E25",
  "topic": "short topic name",
  "book_understanding": {
    "concepts": [
      {"name": "BPLR", "type": "process | comparison | timeline | numbers | definition | cause_effect | mechanism | classification | formula",
       "t_start": 95, "t_end": 180, "prereq_recalled": "what earlier idea is recalled before it, or empty"}
    ],
    "teaching_order": "how the order of the video differs from a textbook's order and why it works (e.g. the problem is shown before the system that fixed it)",
    "breakdown_rule": "one sentence: the rule this video follows to cut the topic into teachable pieces"
  },
  "narration": {
    "opening": {"move": "<move>", "what": "what happens in the first 20 s"},
    "moves": [{"t": 12, "move": "<move>", "concept": "BPLR", "what": "short description in our words"}],
    "story_before_term": [{"term": "base rate", "t_story": 20, "t_term": 70}],
    "examples": [{"t": 20, "kind": "role_play | story | numbers | analogy | real_case | what_if | everyday_object", "what": "...", "carries": "which concept it makes clear"}],
    "closing": {"move": "<move>", "what": "..."},
    "density": "how many new terms per minute, and whether the pace felt right for the level"
  },
  "talmel": [
    {"tile": 3, "t_shown": 27.8, "shown": "what appeared in the red box", "said_gist": "what was being said",
     "naming_word": "the spoken word that names what appeared, exactly as in the tile text (or empty if none)",
     "lead": "picture_first | voice_first | together | unrelated",
     "relation": "shows_the_step | names_the_term | repeats_speech_as_text | adds_new_info | decoration | navigation"}
  ],
  "talmel_summary": "2-3 sentences: how speech and picture fit in this video (does the picture show what the words mean, or only write the words?), what works, what does not",
  "voice": {"notes": "pace, pauses, tone, where the narrator stresses words, how numbers are read"},
  "game_ideas": [
    {"from_t": 238, "mechanic": "run_a_process | allocate | match_partner | build_timeline | place_correctly | cause_chain | market_sim | sort_into_groups | spot_the_error | bargain | other",
     "player_does": "what the learner does", "process_happens": "what the system shows in response",
     "win": "how the learner succeeds", "lose": "what a wrong move shows (and teaches)", "concept": "which concept it trains"}
  ],
  "notes_questions": [
    {"q": "question a notes page answers (Hinglish ok)", "answer_shape": "picture | flow | comparison | table | number | timeline | tree", "from_t": 95}
  ],
  "checks_learned": ["a rule a code check could enforce, learned from what worked or failed here"],
  "teaching_best": [{"t": 20, "why": "..."}],
  "teaching_weak": [{"t": 300, "why": "..."}]
}
```

## Moves (use these words in `move`)

`hook_scene` (a small scene or situation before anything else), `role_play` (dialogue between characters),
`agenda` (says what the video covers), `recall_previous` (reminds an earlier idea or video), `story`,
`example_numbers` (small made-up numbers), `analogy`, `yaani_unpack` (term → plain words), `define_term`,
`cause_chain` (A → B → C), `what_if` (maan lijiye), `contrast` (lekin / jabki), `misconception` (a wrong idea named
and corrected), `conclusion_line` (to yahan saaf hua…), `recap`, `exam_link`, `signpost` (chaliye ab…),
`question_to_viewer`, `human_benefit` (what a person feels or gets), `data_fact` (real figure or date), `mnemonic`.
Add a new move only if none fits, and say so in `what`.

## How to work

1. Read the full transcript `stt2/<ID>.json` (segments with start/end seconds; text is Hindi/Hinglish from speech
   recognition: English terms may appear in Devanagari or Latin; small recognition errors are normal).
2. Read the canvas card `cards3/<ID>.json` (what was shown, segment by segment).
3. Look at every talmel sheet `talmel/<ID>/sheet-NN.jpg` (12 tiles each; each tile: the frame just after a visual
   change, a red box around what changed, and under it the words spoken from 3 s before to 1.5 s after, the word
   nearest the change in [brackets]); `talmel/<ID>/tiles.json` has the same data. Fill one `talmel` row per tile.
4. Write `teach/<ID>.json`, then check by Python that it parses and has every field above.
