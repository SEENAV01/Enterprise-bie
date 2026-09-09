from alignment_engine import build_word_alignment,add_phrase_anchors
from emphasis_pause import add_semantic_events
from audio_contract import audio_contract

def build_alignment(narration_text, word_timestamps, phrases=None, emphasis_terms=None, pause_after_words=None):
    words=build_word_alignment(narration_text,word_timestamps)
    phrases=phrases or []
    if phrases:
        words=add_phrase_anchors(words,phrases)
    words.extend(add_semantic_events(words,emphasis_terms,pause_after_words))
    return {
      "schema_version":"3.7",
      "narration_text":narration_text,
      "anchors":words,
      "contract":audio_contract()
    }
