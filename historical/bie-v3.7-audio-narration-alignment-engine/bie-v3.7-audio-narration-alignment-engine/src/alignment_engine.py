from alignment_types import anchor
from text_units import tokenize

def build_word_alignment(narration_text, word_timestamps):
    tokens=tokenize(narration_text)
    if len(tokens)!=len(word_timestamps):
        raise ValueError("WORD_COUNT_MISMATCH")
    return [
      anchor(
        f"w{i}",
        "WORD",
        ts["start"],ts["end"],
        tok["text"],
        {"word_index":i,"normalized":tok["normalized"]}
      )
      for i,(tok,ts) in enumerate(zip(tokens,word_timestamps))
    ]

def add_phrase_anchors(words, phrase_matches):
    out=list(words)
    for j,p in enumerate(phrase_matches):
        first=words[p["start_word"]]; last=words[p["end_word"]]
        out.append(anchor(
          f"p{j}","PHRASE",first["start"],last["end"],p["phrase"],
          {"start_word":p["start_word"],"end_word":p["end_word"]}
        ))
    return out
