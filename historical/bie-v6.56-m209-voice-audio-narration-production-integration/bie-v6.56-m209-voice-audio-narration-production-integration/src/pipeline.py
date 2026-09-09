from voice import voice,valid as voice_valid
from narration import narration_segment,valid as narration_valid,ordered
from pronunciation import pronunciation,valid as pronunciation_valid
from audio_cues import cue,valid as cue_valid
from audio_timeline import timeline,valid as timeline_valid
from mix import mix_profile,valid as mix_valid
from evidence import evidence_binding,grounded
from provenance import provenance,traceable
from verification import verification,passed

def build_voice_audio_integration():
    v=voice("voice-1","TEACHER","en",None,None,1.0,0.0)

    n1=narration_segment(
        "narr-1","b3",
        "Electric charge is a conserved and quantized property.",
        v["voice_id"],0,55,
        {"electric":"ih-LEK-trik","quantized":"KWON-tized"},
        ["conserved","quantized"]
    )
    n2=narration_segment(
        "narr-2","b4",
        "Like charges repel and unlike charges attract.",
        v["voice_id"],55,50,
        {"repel":"ree-PEL","attract":"uh-TRAKT"},
        ["repel","attract"]
    )

    p1=pronunciation("quantized","KWON-tized",["quantised"],"en")
    p2=pronunciation("electrostatic","ih-LEK-troh-STAT-ik",[],"en")

    cues=[
        cue("cue-1","MUSIC",0,195,"asset://lesson-bed",-18),
        cue("cue-2","DUCK",0,105,None,-8),
        cue("cue-3","FADE_OUT",190,5)
    ]

    tl=timeline([n1,n2],cues)
    mix=mix_profile()
    bindings=[
        evidence_binding("narr-1",["ev-charge"],["record-text-1"]),
        evidence_binding("narr-2",["ev-force"],["record-figure-1"])
    ]
    prov=provenance("audio-1",["script-1"],["sc2","sc3"],
                    ["ev-charge","ev-force"],["artifact://storyboard"])
    check=verification("verify-audio","audio-1","PASS",
                       ["ev-charge","ev-force"])

    return {
        "schema_version":"6.56",
        "voice":v,
        "narration_segments":ordered([n1,n2]),
        "pronunciation":[p1,p2],
        "audio_cues":cues,
        "timeline":tl,
        "mix_profile":mix,
        "evidence_bindings":bindings,
        "provenance":prov,
        "verification":check,
        "quality_gate":{"valid":(
            voice_valid(v)
            and all(narration_valid(n) for n in [n1,n2])
            and all(pronunciation_valid(p) for p in [p1,p2])
            and all(cue_valid(c) for c in cues)
            and timeline_valid(tl)
            and mix_valid(mix)
            and all(grounded(b) for b in bindings)
            and traceable(prov) and passed(check)
        ),"errors":[]}
    }
