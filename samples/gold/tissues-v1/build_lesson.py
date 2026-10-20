"""Writes lesson.json: the gold-sample lesson for 'Tissues and Its Types', Video 1.

Reference sample (Task 038 follow-up, 21 Oct 2026). Script, teaching order and visual direction are
written by Claude acting as BIE's teacher and director, grounded in the chapter PDF (pages cited per
scene). It sets the quality bar the automated pipeline must reach; it is not pipeline output.

``say`` is the narration sent to text-to-speech: Hindi in Devanagari with science terms in English,
so the voice pronounces both correctly (spoken Hinglish). ``cues`` bind on-screen events to words:
the renderer finds ``word`` in the word timings of the beat's audio, else uses ``fallback`` (0-1 of
the beat's speech).
"""
import json
from pathlib import Path


def beat(id, say, *cues):
    return {"id": id, "say": say, "cues": [{"mark": m, "word": w, "fallback": f} for m, w, f in cues]}


VOICE = {
    "model": "gpt-4o-mini-tts",
    "voice": "ash",
    "instructions": (
        "You are a warm, confident Indian science teacher recording a video lesson for UPSC aspirants. "
        "Speak natural Hinglish: Hindi sentences, with English science terms pronounced in clear Indian English. "
        "Moderate pace, slightly slower and stressed on key terms, short natural pauses at dashes and commas. "
        "Sound curious and engaging, like explaining to one student in front of you; never robotic or rushed."
    ),
}

CHAPTER_PLAN = [
    {"video": 1, "title": "Cells ki team aur plant ka growth engine",
     "covers": "Prerequisite: cell, mitosis vs meiosis, mitosis in plants vs animals; tissue; organisation levels; plant tissue map; meristematic tissue (apical, lateral, intercalary)",
     "pages": [87, 95], "minutes": 7},
    {"video": 2, "title": "Permanent tissue I: parenchyma, collenchyma, sclerenchyma",
     "covers": "Differentiation; parenchyma, chlorenchyma, aerenchyma; collenchyma; sclerenchyma fibres and sclereids (coconut husk, seed coats)",
     "pages": [95, 97], "minutes": 7},
    {"video": 3, "title": "Permanent tissue II: xylem aur phloem, plant ki plumbing",
     "covers": "Complex tissue; tracheids, vessels, xylem parenchyma, xylem fibres; sieve cells and tubes, companion cells, phloem fibres and parenchyma; living vs dead",
     "pages": [97, 98], "minutes": 6},
    {"video": 4, "title": "Animal tissue I: epithelial tissue, body ki lining",
     "covers": "Four animal tissue groups; epithelium features; simple squamous, cuboidal, columnar; stratified types; keratinised; transitional (urothelium); glandular",
     "pages": [88, 90], "minutes": 8},
    {"video": 5, "title": "Animal tissue II: connective tissue",
     "covers": "Matrix and fibres (collagen, elastic, reticulate); loose, dense, elastic connective tissue; cartilage, bone, blood, adipose with locations and functions",
     "pages": [90, 94], "minutes": 8},
    {"video": 6, "title": "Animal tissue III: muscle aur nerve",
     "covers": "Skeletal, cardiac, visceral muscle (location, function incl. heat, blood pressure, pupil size, hair erection; appearance; control); neuron and impulse across synapse",
     "pages": [92, 93], "minutes": 7},
    {"video": 7, "title": "Revision aur UPSC practice",
     "covers": "Whole-chapter concept map, statement questions from the chapter's practice set, traps",
     "pages": [98, 100], "minutes": 6},
]

SCENES = [
    {"id": "hook", "component": "Hook", "pages": [], "beats": [
        beat("hook-1", "ज़रा सोचिए। Lawn की घास को ऊपर से काट दो — कुछ ही दिनों में वो फिर से लंबी हो जाती है।",
             ("mow", "काट", 0.45), ("regrow", "फिर", 0.75)),
        beat("hook-2", "और एक पेड़ का तना… हर साल थोड़ा और मोटा होता जाता है। ये बढ़त आती कहाँ से है?",
             ("trunk", "मोटा", 0.45), ("question", "कहाँ", 0.8)),
        beat("hook-3", "इस video के अंत तक आप इसका जवाब एक line में दे पाओगे — और UPSC के एक favourite trap से भी बच जाओगे।",
             ("promise", "UPSC", 0.6)),
    ]},
    {"id": "title", "component": "Title", "pages": [87], "beats": [
        beat("title-1", "Tissues — Part one. Cells की team, और plant का growth engine।", ("subtitle", "Cells", 0.4)),
    ]},
    {"id": "prereq-cell", "component": "CellBuild", "pages": [87], "beats": [
        beat("cell-1", "शुरू करने से पहले, एक मिनट का ज़रूरी revision — क्योंकि आज का पूरा topic cell पर खड़ा है।",
             ("badge", "revision", 0.4)),
        beat("cell-2", "हर cell के बाहर एक cell membrane होती है, अंदर cytoplasm, और बीच में control centre — nucleus।",
             ("membrane", "membrane", 0.25), ("cytoplasm", "cytoplasm", 0.5), ("nucleus", "nucleus", 0.9)),
        beat("cell-3", "Plant cell में दो चीज़ें extra दिखती हैं: बाहर एक मज़बूत cell wall, और अंदर एक बड़ा vacuole।",
             ("plant", "Plant", 0.05), ("wall", "wall", 0.55), ("vacuole", "vacuole", 0.92)),
        beat("cell-4", "ये बड़ा vacuole याद रखना — आज ही हम ऐसी cells देखेंगे जिनमें ये होता ही नहीं।",
             ("remember", "vacuole", 0.2), ("tease", "नहीं", 0.9)),
    ]},
    {"id": "prereq-division", "component": "Division", "pages": [87], "beats": [
        beat("div-1", "Cell बढ़ती कैसे है? Divide होकर। Cell division के दो तरीके हैं — mitosis और meiosis।",
             ("split", "Divide", 0.25), ("mitosis", "mitosis", 0.8), ("meiosis", "meiosis", 0.95)),
        beat("div-2", "Mitosis body की आम cells में होता है — यानी somatic cells में। Nucleus एक बार divide होता है, दो daughter cells बनती हैं, और chromosome number वही रहता है।",
             ("m-somatic", "somatic", 0.3), ("m-once", "एक", 0.5), ("m-two", "दो", 0.68), ("m-chromo", "chromosome", 0.85)),
        beat("div-3", "Meiosis germ cells में होता है। Nucleus दो बार divide होता है, चार daughter cells बनती हैं, और chromosome number आधा हो जाता है — इन्हीं से gametes बनते हैं।",
             ("x-germ", "germ", 0.12), ("x-twice", "दो", 0.35), ("x-four", "चार", 0.5), ("x-half", "आधा", 0.72), ("x-gametes", "gametes", 0.92)),
        beat("div-4", "इसीलिए mitosis को equational division और meiosis को reduction division कहते हैं।",
             ("equational", "equational", 0.35), ("reduction", "reduction", 0.75)),
        beat("div-5", "अब plant और animal का फ़र्क़। Plant cells में centrioles नहीं होते, और division के अंत में बीच में एक cell plate बनती है। Animal cell बीच से दबकर — furrowing से — दो हिस्सों में बँटती है।",
             ("pa", "फ़र्क़", 0.1), ("centrioles", "centrioles", 0.3), ("plate", "plate", 0.55), ("furrow", "furrowing", 0.85)),
        beat("div-6", "और सबसे ज़रूरी बात: animals में mitosis पूरे शरीर के tissues में होता है, लेकिन plants में ये mainly कुछ ख़ास जगहों पर होता है — meristem में। ये शब्द पकड़ के रखिए।",
             ("body", "शरीर", 0.3), ("meristem", "meristem", 0.8)),
    ]},
    {"id": "tissue", "component": "TissueTeam", "pages": [87], "beats": [
        beat("tis-1", "अब असली सवाल — tissue क्या है? जब एक जैसा काम करने वाली cells एक साथ जुड़ जाती हैं, तो उस group को tissue कहते हैं।",
             ("gather", "जुड़", 0.6), ("lock", "group", 0.85)),
        beat("tis-2", "Plant cells मिलकर plant tissues बनाती हैं, और animal cells मिलकर animal tissues।",
             ("plantT", "Plant", 0.1), ("animalT", "animal", 0.65)),
        beat("tis-3", "फ़ायदा? Division of labour. सोचिए एक अकेली cell को खाना बनाना, store करना, transport करना — सब ख़ुद करना पड़े। Overload!",
             ("labour", "labour", 0.15), ("j1", "खाना", 0.45), ("j2", "store", 0.55), ("j3", "transport", 0.65), ("overload", "Overload", 0.95)),
        beat("tis-4", "Tissue बनते ही हर group एक काम संभाल लेता है। हर cell का workload कम होता है — और शरीर में organisation आ जाता है।",
             ("share", "group", 0.3), ("workload", "workload", 0.6), ("organisation", "organisation", 0.9)),
    ]},
    {"id": "ladder", "component": "Ladder", "pages": [87], "beats": [
        beat("lad-1", "यही organisation आगे बढ़ती है: cells से tissue, tissues से organ, organs से organ system, और सब मिलकर पूरा organism।",
             ("l-cell", "cells", 0.22), ("l-tissue", "tissue", 0.35), ("l-organ", "organ", 0.5), ("l-system", "system", 0.7), ("l-organism", "organism", 0.95)),
        beat("lad-2", "Exam में ये order उलट-पुलट करके पूछा जाता है। बस याद रखो: Cell, Tissue, Organ, Organ system, Organism — छोटे से बड़े की तरफ़।",
             ("trap", "उलट", 0.2), ("recite", "Cell", 0.45)),
    ]},
    {"id": "growth", "component": "GrowthCompare", "pages": [87, 94, 95], "beats": [
        beat("gro-1", "अब एक दिलचस्प फ़र्क़। हम इंसान एक उम्र के बाद लंबाई में बढ़ना बंद कर देते हैं। लेकिन पेड़? सौ साल का पेड़ भी नई शाखाएँ और नई जड़ें बनाता रहता है।",
             ("human", "इंसान", 0.25), ("stop", "बंद", 0.45), ("tree", "पेड़", 0.6), ("grow", "शाखाएँ", 0.85)),
        beat("gro-2", "ऐसा इसलिए, क्योंकि plant में कुछ जगहों पर ऐसी cells हमेशा रहती हैं जो लगातार divide होती रहती हैं। इन्हीं से बनता है meristematic tissue — plant का growth engine।",
             ("tips", "जगहों", 0.25), ("divide", "divide", 0.5), ("engine", "engine", 0.92)),
        beat("gro-3", "Plant tissues के दो बड़े groups हैं: meristematic, जो divide होते रहते हैं, और permanent, जो divide होना छोड़कर एक पक्का काम चुन लेते हैं। आज हम meristematic को गहराई से देखेंगे।",
             ("map", "groups", 0.15), ("map-mer", "meristematic", 0.25), ("map-perm", "permanent", 0.55), ("focus", "आज", 0.85)),
    ]},
    {"id": "meristem-cells", "component": "MeristemZoom", "pages": [95], "beats": [
        beat("mz-1", "Root की tip पर zoom करते हैं। यहाँ की cells छोटी हैं — गोल, oval या rectangular — और एक-दूसरे से बिल्कुल सटी हुई।",
             ("zoom", "zoom", 0.2), ("shapes", "oval", 0.55), ("packed", "सटी", 0.9)),
        beat("mz-2", "इनके बीच intercellular spaces नहीं होते — इसलिए इन्हें compactly packed कहते हैं।",
             ("spaces", "spaces", 0.3), ("compact", "compactly", 0.75)),
        beat("mz-3", "और याद है वो बड़ा vacuole? Meristematic cells में vacuole होता ही नहीं। Nucleus बड़ा, और cytoplasm घना।",
             ("vac", "vacuole", 0.25), ("novac", "नहीं", 0.6), ("bignuc", "Nucleus", 0.8)),
        beat("mz-4", "क्योंकि इनका एक ही काम है — divide होना, बार-बार। ये plant की सबसे active cells हैं।",
             ("dividing", "divide", 0.35), ("active", "active", 0.85)),
        beat("mz-5", "Checklist बना लो: जगह — growing regions। Intercellular spaces — absent। Vacuole — absent। काम — सिर्फ़ cell division।",
             ("c1", "growing", 0.2), ("c2", "spaces", 0.45), ("c3", "Vacuole", 0.68), ("c4", "division", 0.95)),
    ]},
    {"id": "apical", "component": "PlantZones", "zone": "apical", "pages": [95], "beats": [
        beat("ap-1", "Meristem तीन जगह मिलता है। पहला — apical meristem। Apex यानी tip। ये root की tip और shoot की tip पर होता है।",
             ("three", "तीन", 0.1), ("label", "apical", 0.3), ("shootTip", "shoot", 0.85), ("rootTip", "root", 0.7)),
        beat("ap-2", "इसका काम: root और shoot की लंबाई बढ़ाना। Shoot ऊपर, root नीचे — दोनों tips से plant लंबा होता है।",
             ("grow", "लंबाई", 0.3), ("up", "ऊपर", 0.55), ("down", "नीचे", 0.7)),
    ]},
    {"id": "lateral", "component": "PlantZones", "zone": "lateral", "pages": [95], "beats": [
        beat("lat-1", "दूसरा — lateral meristem। Lateral यानी side। ये bark के ठीक नीचे होता है — तने के चारों ओर एक घेरे की तरह।",
             ("label", "lateral", 0.15), ("bark", "bark", 0.55), ("ring", "घेरे", 0.9)),
        beat("lat-2", "ये लंबाई नहीं, मोटाई बढ़ाता है — root या stem की girth। इसीलिए पेड़ का तना हर साल और मोटा होता जाता है।",
             ("thick", "मोटाई", 0.25), ("girth", "girth", 0.5), ("answer", "इसीलिए", 0.7)),
    ]},
    {"id": "intercalary", "component": "PlantZones", "zone": "intercalary", "pages": [95], "beats": [
        beat("int-1", "तीसरा — intercalary meristem। ये leaves के base पर या internodes पर होता है — यानी दो nodes के बीच वाले हिस्से में।",
             ("label", "intercalary", 0.15), ("base", "base", 0.45), ("internode", "internodes", 0.65), ("nodes", "nodes", 0.9)),
        beat("int-2", "ये leaves और internodes जैसे हिस्सों की लंबाई बढ़ाता है।", ("stretch", "लंबाई", 0.7)),
        beat("int-3", "अब हमारी घास वाली पहेली! घास का growth zone ऊपर tip पर नहीं, नीचे leaf के base पर होता है। ऊपर से काटो, तो engine बचा रहता है — और घास फिर उग आती है।",
             ("grass", "घास", 0.15), ("zone", "base", 0.45), ("cut", "काटो", 0.65), ("regrow", "उग", 0.92)),
    ]},
    {"id": "summary", "component": "SummaryTable", "pages": [95], "beats": [
        beat("sum-1", "एक table में समेट लेते हैं।", ("table", "table", 0.4)),
        beat("sum-2", "Apical — root और shoot की tip पर — लंबाई।", ("row", "Apical", 0.05)),
        beat("sum-3", "Lateral — bark के नीचे — girth, यानी मोटाई।", ("row", "Lateral", 0.05)),
        beat("sum-4", "Intercalary — leaves के base या internodes पर — उनकी लंबाई।", ("row", "Intercalary", 0.05)),
    ]},
    {"id": "traps", "component": "ExamTraps", "pages": [87, 95], "beats": [
        beat("trap-1", "अब UPSC वाले traps।", ("intro", "traps", 0.5)),
        beat("trap-2", "Trap एक: Lateral meristem plant की लंबाई बढ़ाता है — ग़लत! Lateral मोटाई बढ़ाता है। लंबाई बढ़ाते हैं apical और intercalary।",
             ("wrong", "ग़लत", 0.45), ("fix", "मोटाई", 0.65)),
        beat("trap-3", "Trap दो: Meristematic cells में बड़ा central vacuole होता है — ग़लत! बड़ा central vacuole permanent tissue की पहचान है; meristem में vacuole absent है।",
             ("wrong", "ग़लत", 0.4), ("fix", "permanent", 0.65)),
        beat("trap-4", "Trap तीन: Plants में mitosis पूरे शरीर में बराबर होता है — ग़लत! Plants में mitosis mainly meristem में होता है।",
             ("wrong", "ग़लत", 0.5), ("fix", "meristem", 0.85)),
    ]},
    {"id": "next", "component": "Bridge", "pages": [95], "beats": [
        beat("next-1", "तो meristem की cells divide होती रहती हैं। लेकिन जब कोई cell divide होना छोड़कर एक पक्की shape, size और काम चुन लेती है — उस process को differentiation कहते हैं, और यहीं से बनते हैं permanent tissues।",
             ("stop", "छोड़कर", 0.3), ("differentiate", "differentiation", 0.7), ("permanent", "permanent", 0.95)),
        beat("next-2", "अगली video में: parenchyma, collenchyma और sclerenchyma — और ये भी कि नारियल का छिलका इतना सख़्त क्यों होता है। तब तक game खेलकर आज का revision कर लो!",
             ("next", "parenchyma", 0.15), ("coconut", "नारियल", 0.6), ("game", "game", 0.85)),
    ]},
]

LESSON = {
    "lesson_id": "tissues-v1",
    "kind": "GOLD_REFERENCE_SAMPLE",
    "status_note": "Directed by Claude in session; quality bar for the pipeline; not pipeline output; not accepted.",
    "source": {"title": "Science and Technology - 10. Tissues and Its Types", "pdf_sha256": "05616c29dd08d715424c0ae242097ddc82c3fefc48d9e009db09ce371ae7db7d",
               "branch": "blindtest-inputs", "path": "chapters/tissues-and-its-types.pdf"},
    "audience": "UPSC / State PCS aspirants", "language": "Hinglish",
    "video": {"number": 1, "title": "Tissues · Part 1: Cells ki team aur plant ka growth engine", "fps": 30, "width": 1920, "height": 1080},
    "voice": VOICE, "chapter_plan": CHAPTER_PLAN, "scenes": SCENES,
}

if __name__ == "__main__":
    out = Path(__file__).with_name("lesson.json")
    out.write_text(json.dumps(LESSON, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    beats = [b for s in SCENES for b in s["beats"]]
    words = sum(len(b["say"].split()) for b in beats)
    print(f"{len(SCENES)} scenes, {len(beats)} beats, {words} words, ~{words / 140:.1f} min at 140 wpm")
