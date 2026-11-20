"""Dikhaya-bola, the shown-said check (Navin, 5 November 2026): "jo bola, woh dikhe" — every thing a line names is on
screen during that line.

Navin's choice (decision card, 5 November 2026): "Boli cheez usi line mein" — when a line names a thing, a person's
thing or a place that BIE can draw, that thing is on screen while the line is spoken; when it is not, the compiler
returns the plan naming the line and the word; the target is 95% or more of the lines (agreement of 3 November,
section 5: every line "said = shown").

Which words count: the Hindi and English words of the saancha library (``saanche.json`` tags) that name concrete things
— a sack, a note, a coin, a dollar, a bank, a vault, a phone. Diagrams and marks (a timeline, a graph, a tick, a fork,
a gauge) and abstract words (price, demand, savings, payment) are ways of showing, not things said, so they create no
obligation; nor do ordinary words that a tag happens to spell (STOP: बस "only", बीच, दिन, समय, income, table) or a tag
that only a diagram saancha carries (DIAGRAMS: causeChain, pieChart, formula). A word is matched as a whole word with
its common Hindi endings (नोट → नोटों, रुपया → रुपये) and English plurals: बस is not in "bus", आग is not in आगे.

What shows a word: during the line (at least 1 s of it, or half of a shorter line), an element on screen that is one
of the saanche carrying that word — drawn alone, in a group, held by a person or inside a thought bubble — or a drawn
thing whose own label carries the word (a sack labelled "नमक" shows salt) at that second, its steps included: a label
or a graph title that a step changes on the cue word shows the word from then on (the Money v2 craft). A word that names a place is also shown by the
place the scene stands in (its background or a world item of that kind: दुकान in the shop, पंप in the petrol pump), and
by the world's own sign and spot names (its label and signs are written on the place). A text alone is not the thing, and
a world never shows an object it does not draw or write (a bank hall shows "बैंक" the place, not a coin).
"""
from __future__ import annotations

import re

from bie.brain import saanche

STEP = 0.5
MIN_SHOWN = 1.0                 # seconds of the line the thing must be on screen (half of a shorter line)
TARGET = 0.95                   # agreement: every line said = shown, 95% or more

# Saanche that are a way of showing (diagrams, marks, scales, metaphors, the place itself), not a thing that is named.
NOT_THINGS = {"mark", "disc", "segmentedBar", "ruler", "pillars", "podium", "staircase", "rope", "world", "flow", "bands",
              "fork", "gapBars", "timeline", "table", "graph", "funnel", "roadmap", "gauge", "hands", "sweat", "priceTag",
              "crowd", "plant", "barrier", "chair"}
# Words too general to oblige a drawing on every line that says them (a money lesson says पैसा in every line), or that
# name an idea rather than a thing.
ABSTRACT = {"पैसा", "पैसे", "धन", "money", "cash", "funds", "fund", "wealth", "currency", "भुगतान", "payment", "बचत",
            "savings", "भंडार", "आरक्षित", "reserve", "reserves", "संस्था", "institution", "इमारत", "building", "ढेर",
            "heap", "pile", "stack", "डिब्बा", "can", "box", "जगह", "place", "स्थान", "मूल्य", "दाम", "क़ीमत", "price",
            "cost", "पद", "आसन", "seat", "post", "निवेश", "invest", "फंड", "गाड़ी", "ईंट", "brick", "पत्ते", "leaves",
            "रेटिंग", "rating", "पैमाना", "scale", "मीटर", "meter", "सूचकांक", "index", "रुकावट", "बाधा", "प्रतिबंध",
            "ban", "मेहनत", "पसीना", "effort", "बैठक", "deal", "case", "card", "tag", "bar", "line", "share", "check",
            "bill", "tie", "block", "branch", "शाखा", "port", "mark", "rate", "split", "parts", "types", "real", "public",
            "people", "लोग", "जनता", "भीड़", "आबादी", "crowd", "population", "sick unit", "small lender", "lender",
            "bundle", "notes", "note", "roll", "packet", "पैकेट", "bag", "bowl", "pot", "jar", "safe", "lock", "ताला",
            "chain", "rod", "rope", "seed", "grow", "tree", "tool", "औज़ार", "exchange", "market", "financial market",
            "bond", "act", "law", "report", "licence", "contract", "proposal", "document", "balance", "balances"}
# The place a scene stands in (its background, or a world item's kind) shows a word that names that place: a line that
# says दुकान while the scene stands in the shop shows the shop. The names are the engine's own backgrounds and world kinds.
PLACES = {"village": {"गाँव", "village"}, "haat": {"हाट", "बाज़ार", "market"}, "shop": {"दुकान", "shop"},
          "store": {"दुकान", "गोदाम", "shop", "store", "warehouse"}, "market": {"बाज़ार", "market"},
          "bankHall": {"बैंक", "bank"}, "centralBank": {"केंद्रीय बैंक", "रिज़र्व बैंक", "आरबीआई", "central bank",
          "reserve bank", "rbi", "बैंक", "bank"}, "exchangeFloor": {"शेयर बाज़ार", "बाज़ार"}, "port": {"बंदरगाह"},
          "factory": {"कारख़ाना", "उद्योग", "factory", "industry"}, "office": {"दफ़्तर", "office"},
          "court": {"अदालत", "न्यायालय", "court"}, "city": {"शहर", "city"}, "assembly": {"संसद", "सभा", "parliament",
          "assembly"}, "twoCountries": {"दो देश", "border"}, "forexCounter": {"विदेशी मुद्रा", "मुद्रा विनिमय", "forex",
          "foreign currency", "काउंटर", "counter"},
          # the newer worlds and backgrounds name themselves and their numbered spots (Sloman workers, Nov 2026: about 20
          # boards a video were added only so the checker saw "पंप" in the petrol-pump world)
          "mandi": {"मंडी", "mandi", "बाज़ार", "बाजार", "market", "ढेर", "अनाज"}, "foodStreet": {"गली", "street", "food street",
          "ठेला", "ठेले", "स्टॉल", "stall", "दुकान", "shop"}, "labourChowk": {"चौक", "मज़दूर चौक", "मजदूर चौक", "मज़दूर", "मजदूर",
          "labour", "worker", "workers"}, "factoryFloor": {"कारख़ाना", "कारखाना", "फ़ैक्टरी", "फैक्टरी", "factory", "मशीन", "machine"},
          "farm": {"खेत", "farm", "field", "किसान", "farmer"}, "riverTown": {"नदी", "river", "क़स्बा", "कस्बा", "town", "नाव", "boat"},
          "mohalla": {"मोहल्ला", "गली", "street", "घर", "मकान", "house"}, "canteen": {"कैंटीन", "canteen", "मेन्यू", "menu", "कॉलेज",
          "college"}, "home": {"घर", "home", "house", "मकान"}, "teaEstate": {"बागान", "चाय बागान", "tea estate", "चाय", "tea"},
          "busStand": {"बस स्टैंड", "बस अड्डा", "bus stand", "bus", "बस"}, "petrolPump": {"पेट्रोल पंप", "petrol pump", "पंप", "pump",
          "पेट्रोल", "petrol", "डीज़ल", "डीजल", "diesel", "fuel", "ईंधन"}, "venue": {"हॉल", "hall", "venue", "मंच", "stage", "सभागार"},
          "godown": {"गोदाम", "godown", "warehouse", "बोरी", "बोरियाँ", "sack", "sacks"}, "island": {"टापू", "द्वीप", "island"},
          "twoSector": {"खेत", "farm", "कारख़ाना", "कारखाना", "factory"}, "dealingRoom": {"डीलिंग रूम", "dealing room", "स्क्रीन",
          "screen", "screens", "trader", "traders"}, "hospital": {"अस्पताल", "hospital", "डॉक्टर", "doctor", "क्लिनिक", "clinic"},
          "foodShop": {"दुकान", "shop", "बेकरी", "bakery", "ओवन", "oven", "भट्टी"}}
# a world's sign and spot words (its label, its signs) are written on the place: they show what they name
WORLD_WORD_PARAMS = ("label", "signs", "title", "name")
# Saanche that draw an idea, a process or a chart (a cause chain, a pie, a formula, a poverty line): their tags name the
# idea, so a tag that only such a saancha carries creates no obligation (pilot ch02 v1: income -> incomeLine, effect ->
# causeChain, बिंदु -> scatterFit, बीच -> spectrum, गिनी -> barChart). They still show a thing through their labels, and
# a tag that a concrete thing also carries (घड़ी: dayHours and clock) still obliges it.
DIAGRAMS = {"accountBar", "agents", "balanceSheet", "barChart", "causeChain", "chainRounds", "choicePaths", "circularFlow",
            "contagion", "cycleWave", "dayHours", "doorway", "formula", "gambleTree", "iconArray", "incomeLine",
            "insurancePool", "layers", "marginalBars", "moneySplit", "oneVsAll", "padlocks", "pieChart", "pricePath",
            "rateCorridor", "riskDial", "roundBars", "scatterFit", "securitisation", "shareBar", "sorter", "spectrum",
            "tAccount", "timeSeries", "timeValue", "tradeLedger", "tugOfWar", "waterfall", "weightBars"}
# Ordinary words that some tag spells but that name no thing when said: Hindi function and time words, and the
# lesson's abstract words (pilot ch02 v1: बस "only" -> bus, दिन/काम/कमाई -> dayHours, चित्र -> pictogram, समय -> clock,
# साल -> timeSeries, table "a data table" -> desk). The English "bus" still names a bus.
STOP = {"बस", "बीच", "दिन", "काम", "कमाई", "गिनी", "गिने", "गिनती", "चित्र", "चित्रों", "बिंदु", "रेखा", "कुल", "जोड़", "समय",
        "साल", "महीना", "महीने", "हफ़्ता", "हफ़्ते", "घंटे", "दौर", "असर", "प्रभाव", "हिस्सा", "हिस्से", "हिसाब", "छूट",
        "शर्त", "विकल्प", "लोग", "तुलना", "स्थिति", "पहचान", "सूची", "स्तर", "बदलाव", "योगदान", "चरण", "मान",
        "effect", "income", "table", "mechanism", "count", "time", "day", "days", "year", "years", "month", "hours", "work",
        "model", "trend", "threshold", "level", "flow", "rounds", "choice", "options", "risk", "chance",
        # too vague to demand a drawing (Sloman workers, Nov 2026): फल is also "result", stock a stock of anything,
        # उत्पादन "production", board any board, जोखिम "risk"; खाते is mostly "(they) eat"
        "फल", "stock", "उत्पादन", "board", "जोखिम", "खाते", "सूखा"}
# Said forms that look like a tag plus an ending but are other words: आगे (ahead) is not आग (fire) + े.
NOT_FORMS = {"आगे", "बसे", "बसा", "बसी", "बसें", "दिना", "तेली", "नोटा",
             # verb forms that look like a thing word plus an ending (Sloman workers, Nov 2026): करो/करें/करते are "do",
             # not कर "tax"; खाती is "eats", not खाता "account"
             "करो", "करें", "करे", "करते", "करता", "करती", "करेंगे", "करेगा", "करेगी", "करना", "करने", "करनी", "करके",
             "करवाते", "कराते", "खाती"}
# A thing word that is also a verb (कर "tax" / कर "do", खाता "account" / खाता "eats"): read as the verb when the next
# word is a helper verb (कर लें, कर दिया, कर सकते; खाते हैं, खाता है). Real uses (कर बढ़ा, कर दर, बैंक खाते में) still count.
VERB_TAGS = {
    "खाता": {"है", "हैं", "था", "थे", "थी", "हो", "हूँ", "रहा", "रहे", "रही", "जाता", "जाते"},
}
# कर followed by a light or helper verb in any form is "do" (Sloman workers, Nov 2026: कर देंगी, कर दिए, कर लेंगे,
# कर लीजिए, कर दीजियेगा, कर पाएँगे, कर डालिए): the general pattern is a light-verb stem (दे/दि/दी/दो, ले/लि/ली/लो, सक,
# रह, चुक, पा, डाल, बैठ, उठ, जा/गय/गए/गई) with a verb ending (-ता/-ते/-ती, -ना/-ने/-नी, -गा/-गे/-गी, -एँ/-ें, -ए/-या, -इए/
# -ीजिए/-ीजियेगा, -ो, -कर). Not verbs: कर देय "tax payable", कर दाता, कर दर, कर लगा, कर राजस्व, कर जाल.
_END = r"(?:|ं|ँ|[ाीेो]|ें|त[ाीे]|न[ाीे]|ग[ाीे]|ंग[ेी]|ँग[ेी]|एँ|एं|ए|या|ये|यी|इए|िए|िये|िएगा|ियेगा|कर|ो)"
KAR_VERB = re.compile(
    r"^(?:(?:दे|दें|दो)" + _END + r"|दे(?:त[ाीे]|न[ाीे]|ग[ाीे]|ंग[ेी]|ँग[ेी])|दिय[ाेी]|दिए|दी|दीं|दीजि(?:ए|ये|येगा|एगा)|दिलवा\w*"
    r"|ले" + _END + r"|लो|लिय[ाेी]|लिए|ली|लीं|लीजि(?:ए|ये|येगा|एगा)|लू[ँं](?:गा|गी)?"
    r"|सक" + _END + r"|सकूँ|सकूं|सकें|रह" + _END + r"|चुक" + _END + r"|पा(?:ए|एँ|एं|एँग[ेी]|एंग[ेी]|एग[ाीे]|ओ|ऊँ|ते|ता|ती|ना|ने|या|यी|ये|येंगे)"
    r"|डाल" + _END + r"|बैठ" + _END + r"|उठ" + _END + r"|जात[ाीे]|जाए|जाएँ|जाएं|जाना|जाने|जाएग[ाीे]|जाएंग[ेी]|जाएँग[ेी]|जाओ|जाइए"
    r"|गया|गए|गई|गयी|गये)$")
# "दो" after कर is also "two" (कर दो प्रकार के होते हैं): followed by a counted noun it is the number, not the verb.
_TWO_NOUNS = {"प्रकार", "तरह", "किस्म", "क़िस्म", "तरीके", "तरीक़े", "रूप", "हिस्से", "हिस्सों", "स्तर", "स्तरों", "भाग", "भागों", "चीज़ें", "चीजें",
              "दर", "दरें", "देश", "देशों", "साल", "बार"}
_KAR_SKIP = {"नहीं", "न", "भी", "ही", "तो"}
PUNCT = "।॥?!,.;:…\"'“”‘’()[]{}-–—"


def _clean(tok: str) -> str:
    """A word with the Hindi and English punctuation round it taken off (कर दे। -> दे)."""
    return str(tok or "").strip(PUNCT + " ")


# Hindi names of English thing words (and back): a Hindi label shows an English word said in the narration, and an
# English label a Hindi one (डीज़ल = diesel, कारख़ाना = factory, कर = tax).
ALIAS_GROUPS = (
    ("diesel", "डीज़ल", "डीजल"), ("petrol", "पेट्रोल"), ("factory", "फ़ैक्टरी", "फैक्टरी", "फ़ैक्ट्री", "फैक्ट्री", "कारख़ाना", "कारखाना"),
    ("tax", "कर", "टैक्स"), ("pound", "पाउंड", "पौंड"), ("dollar", "डॉलर"), ("euro", "यूरो"), ("rupee", "रुपया", "रुपये"),
    ("bank", "बैंक"), ("shop", "दुकान"), ("market", "बाज़ार", "बाजार", "मंडी"), ("farmer", "किसान"), ("worker", "मज़दूर", "मजदूर"),
    ("car", "कार", "गाड़ी"), ("house", "घर", "मकान"), ("coin", "सिक्का"), ("note", "नोट"), ("loan", "क़र्ज़", "कर्ज", "ऋण"),
    ("oil", "तेल"), ("wheat", "गेहूँ", "गेहूं"), ("rice", "चावल"), ("phone", "फ़ोन", "फोन"), ("train", "ट्रेन", "रेल"),
    ("plane", "हवाई जहाज़", "विमान"), ("ship", "जहाज़", "जहाज"), ("government", "सरकार"), ("company", "कंपनी"),
    ("ticket", "टिकट"), ("salary", "वेतन", "तनख़्वाह"), ("price", "कीमत", "क़ीमत", "दाम"), ("gold", "सोना"), ("electricity", "बिजली"),
    # economics terms (Sloman workers, Nov 2026): a Hindi label shows the English word said, and back
    ("marginal cost", "सीमांत लागत", "mc"), ("marginal revenue", "सीमांत आय", "सीमांत राजस्व", "mr"),
    ("marginal utility", "सीमांत उपयोगिता", "mu"), ("marginal product", "सीमांत उत्पाद"), ("average cost", "औसत लागत", "ac", "atc"),
    ("total cost", "कुल लागत", "tc"), ("fixed cost", "स्थिर लागत", "बंधी लागत", "fc"), ("variable cost", "परिवर्ती लागत", "vc"),
    ("opportunity cost", "अवसर लागत"), ("total revenue", "कुल आय", "कुल राजस्व", "tr"), ("average revenue", "औसत आय", "ar"),
    ("cost", "लागत"), ("revenue", "राजस्व", "आमदनी"), ("profit", "लाभ", "मुनाफ़ा", "मुनाफा", "प्रॉफिट"), ("loss", "हानि", "घाटा", "नुकसान", "नुक़सान"),
    ("demand", "माँग", "मांग"), ("supply", "आपूर्ति", "पूर्ति", "सप्लाई"), ("demand curve", "माँग वक्र", "मांग वक्र"),
    ("supply curve", "आपूर्ति वक्र", "पूर्ति वक्र"), ("equilibrium", "संतुलन"), ("elasticity", "लोच"), ("budget line", "बजट रेखा"),
    ("indifference curve", "तटस्थता वक्र", "उदासीनता वक्र"), ("utility", "उपयोगिता"), ("output", "उत्पादन", "उत्पाद"),
    ("offer", "प्रस्ताव", "ऑफ़र", "ऑफर", "पेशकश"), ("bid", "बोली"), ("auction", "नीलामी"), ("account", "खाता", "खाते", "अकाउंट"),
    ("bank account", "बैंक खाता", "बैंक खाते"), ("insurance", "बीमा", "इंश्योरेंस"), ("premium", "प्रीमियम", "किस्त", "क़िस्त"),
    ("policy", "पॉलिसी"), ("claim", "दावा", "क्लेम"), ("pension", "पेंशन"), ("interest", "ब्याज"), ("interest rate", "ब्याज दर"),
    ("deposit", "जमा राशि", "डिपॉज़िट"), ("cheque", "चेक"), ("receipt", "रसीद"), ("invoice", "बिल"), ("wage", "मज़दूरी", "मजदूरी"),
    ("wages", "मज़दूरी", "मजदूरी"), ("rent", "किराया"), ("land", "ज़मीन", "जमीन", "भूमि"), ("capital", "पूँजी", "पूंजी"),
    ("labour", "श्रम"), ("labor", "श्रम"), ("machine", "मशीन"), ("tractor", "ट्रैक्टर"), ("crop", "फसल", "फ़सल"), ("budget", "बजट"),
    ("subsidy", "सब्सिडी", "अनुदान"), ("tariff", "टैरिफ़", "टैरिफ", "शुल्क", "सीमा शुल्क"), ("duty", "शुल्क"), ("quota", "कोटा"),
    ("inflation", "महँगाई", "महंगाई", "मुद्रास्फीति"), ("unemployment", "बेरोज़गारी", "बेरोजगारी"), ("export", "निर्यात"),
    ("import", "आयात"), ("exports", "निर्यात"), ("imports", "आयात"), ("consumer", "उपभोक्ता", "ग्राहक"), ("customer", "ग्राहक"),
    ("producer", "उत्पादक"), ("buyer", "ख़रीदार", "खरीदार"), ("seller", "विक्रेता", "बेचने वाला"), ("firm", "फ़र्म", "फर्म"),
    ("monopoly", "एकाधिकार"), ("cartel", "कार्टेल"), ("contract", "अनुबंध", "कॉन्ट्रैक्ट", "करार"), ("warranty", "वारंटी"),
    ("guarantee", "गारंटी"), ("lottery", "लॉटरी"), ("gamble", "जुआ"), ("bet", "दाँव", "दांव"), ("dice", "पासा", "पासे"),
    ("queue", "कतार", "क़तार", "लाइन"), ("ration card", "राशन कार्ड"), ("credit card", "क्रेडिट कार्ड"), ("debit card", "डेबिट कार्ड"),
    ("wallet", "बटुआ", "वॉलेट"), ("share", "शेयर"), ("shares", "शेयर"), ("stock market", "शेयर बाज़ार", "शेयर बाजार"),
    ("bond", "बॉन्ड", "बांड"), ("gdp", "जीडीपी", "सकल घरेलू उत्पाद"), ("budget deficit", "बजट घाटा"), ("savings", "बचत"),
    ("investment", "निवेश"), ("wealth", "संपत्ति", "दौलत"), ("asset", "परिसंपत्ति", "संपत्ति"), ("debt", "ऋण", "क़र्ज़", "कर्ज"),
    ("truck", "ट्रक"), ("milk", "दूध"), ("water", "पानी", "जल"), ("sugar", "चीनी"), ("salt", "नमक"), ("sack", "बोरी"),
    ("vehicle", "वाहन", "गाड़ी"), ("car insurance", "कार बीमा", "वाहन बीमा"), ("health insurance", "स्वास्थ्य बीमा"),
    ("used car", "पुरानी कार", "पुरानी गाड़ी"), ("employer", "मालिक", "नियोक्ता"), ("union", "यूनियन", "संघ"),
)
_ALIAS: dict = {}
for _g in ALIAS_GROUPS:
    for _w in _g:
        _ALIAS.setdefault(_w, set()).update(x for x in _g if x != _w)


def aliases(tag: str) -> set:
    """Other-language names of a thing word (lower case), for matching a label against what was said."""
    return set(_ALIAS.get(str(tag or "").strip().lower(), ()))


# Ideas a drawing shows without spelling them: a shortage is a gap (gapBars, a graph's gaps), rationing a ration card.
SHOWN_BY = {"shortage": lambda d, p: d == "gapBars" or (d == "graph" and bool(str(p.get("gaps") or "").strip())),
            "rationing": lambda d, p: d == "slip" and p.get("kind") == "rationCard"}
for _w, _k in (("कमी", "shortage"), ("अभाव", "shortage"), ("राशनिंग", "rationing"), ("राशन", "rationing")):
    SHOWN_BY[_w] = SHOWN_BY[_k]


def _verb_at(toks: list, i: int, tag: str) -> bool:
    """Token ``i`` (a match of ``tag``) is the verb that shares the thing word's spelling: the next word is a helper."""
    if i + 1 >= len(toks):
        return False
    nxt = _clean(toks[i + 1])
    if tag == "कर":
        if nxt == "दो" and i + 2 < len(toks) and _clean(toks[i + 2]) in _TWO_NOUNS:
            return False
        if nxt in _KAR_SKIP and i + 2 < len(toks):  # कर नहीं सकती, कर भी देगी, कर ही लेंगे
            nxt = _clean(toks[i + 2])
        return bool(KAR_VERB.match(nxt))
    return nxt in VERB_TAGS.get(tag, ())


# A word that names a thing only in some contexts: लाइन is a queue only when the line also says कतार/queue or people
# stand in it (तीन लाइन लिखिए is a line of text).
CONTEXT_ONLY = {"लाइन": ("कतार", "क़तार", "कतारें", "queue", "खड़े", "खड़ा", "खड़ी", "खड़े", "इंतज़ार", "इंतजार", "wait", "लगे", "लगी",
                       "लगना", "लगते", "लगती", "लगाना", "लगाते", "टिकट", "राशन", "खिड़की", "काउंटर")}
# Idioms whose thing word names no thing: पासा पलटना "the tables turn" (पासा पलटिए, पासा पलट गया); पानी फेरना "to ruin".
IDIOMS = {"पासा": ("पलट",), "पासे": ("पलट",), "पानी": ("फेर", "फिर"), "पत्ता": ("कट", "साफ़"), "घी": ("के दिए", "के दीये")}


def _idiom_at(toks: list, i: int, tag: str) -> bool:
    nxt = " ".join(_clean(t) for t in toks[i + 1:i + 3])
    return any(nxt.startswith(w) for w in IDIOMS.get(_clean(toks[i]), ()) + IDIOMS.get(tag, ()))


# A word that names no thing in some contexts: डिग्री/degree after a number or in a line about angles, graphs or lines is
# an angle (45 डिग्री की रेखा), not a degree certificate.
_NUM = re.compile(r"^[\d.,०-९]+°?$")
NOT_IN_CONTEXT = {w: ("कोण", "angle", "रेखा", "line", "graph", "ग्राफ़", "ग्राफ", "वक्र", "curve", "ढलान", "slope", "अक्ष", "axis",
                      "°", "घुमाव", "तापमान", "temperature", "सेल्सियस", "celsius")
                  for w in ("डिग्री", "degree", "degrees")}


# A thing word that names a country or a body after these words: सोवियत संघ / Soviet Union is a country, यूरोपीय संघ /
# European Union a group of countries, not a trade union.
NOT_AFTER = {w: ("सोवियत", "soviet", "यूरोपीय", "european", "राष्ट्र", "राष्ट्रों", "अफ्रीकी", "african", "अफ़्रीकी", "postal", "customs",
                 "सीमा", "monetary", "मौद्रिक")
             for w in ("संघ", "union", "यूनियन")}


def _context_ok(toks: list, tag: str, i: int | None = None) -> bool:
    if i is not None and i > 0 and _clean(toks[i - 1]) in NOT_AFTER.get(tag, ()):
        return False
    need = CONTEXT_ONLY.get(tag)
    if need and not any(_clean(t) in need for t in toks):
        return False
    bad = NOT_IN_CONTEXT.get(tag)
    if bad:
        if i is not None and i > 0 and _NUM.match(_clean(toks[i - 1])):
            return False
        if any(_clean(t) in bad for t in toks):
            return False
    return True


SUFFIXES = ("ों", "ो", "ें", "े", "ियों", "ियाँ", "यों", "एँ", "ाओं", "ाएँ")   # plural and oblique endings only: जार + ी is जारी
STEM_ENDINGS = ("ा", "े", "ों", "ें", "ी", "ियाँ", "ियों")                             # रुपया -> रुपये, सिक्का -> सिक्कों
TOKEN = re.compile(r"[\wऀ-ॿ][\wऀ-ॿ़ँ-ःा-्'-]*")


def lexicon() -> dict:
    """word (lower case) -> the thing-saanche that carry it; multi-word tags kept as phrases."""
    out: dict = {}
    for name, entry in saanche.manifest()["saanche"].items():
        if name in NOT_THINGS:
            continue
        for tag in entry.get("tags") or []:
            word = tag.strip().lower()
            if not word or word in ABSTRACT or word in STOP or len(word) < 2:
                continue
            out.setdefault(word, set()).add(name)
    # a word only diagrams carry names their idea, not a thing (they still show it, by name, where a thing carries it too)
    return {w: names for w, names in out.items() if names - DIAGRAMS}


def tokens(text: str) -> list:
    """The whole words of a text (Devanagari with its signs, or Roman), lower case: the units every match is made on."""
    return [m.group(0).strip("'-।॥") for m in TOKEN.finditer(str(text or "").lower())]


def _phrase_at(toks: list, i: int, words: list) -> bool:
    """The tag ``words`` (a phrase split into words) is said at token ``i``: whole words, the last with its endings."""
    if i + len(words) > len(toks):
        return False
    return all(toks[i + k] == words[k] for k in range(len(words) - 1)) and _stem_match(toks[i + len(words) - 1], words[-1])


def has_word(text: str, tag: str) -> bool:
    """``tag`` is said or written in ``text`` as whole words (with the tag's endings): बस is not in "bus", आग not in आगे."""
    toks, words = tokens(text), tokens(tag)
    if not words:
        return False
    return any(_phrase_at(toks, i, words) and not (len(words) == 1 and _verb_at(toks, i, words[0])) for i in range(len(toks)))


def _stem_match(token: str, word: str) -> bool:
    if token == word:
        return True
    if token in NOT_FORMS or token in STOP:
        return False
    if re.fullmatch(r"[a-z][a-z .-]*", word):
        return token in (word + "s", word + "es")
    if len(word) >= 2 and token.startswith(word) and token[len(word):] in SUFFIXES:
        return True
    if word[-1] in "ाी" and len(word) >= 3:
        stem = word[:-1]
        return token.startswith(stem) and token[len(stem):] in STEM_ENDINGS
    return False


def named_things(text: str, lex: dict | None = None) -> list:
    """The thing-words a line names, in order: [(word as said, tag, saanche)]; phrases before single words."""
    lex = lex if lex is not None else lexicon()
    low = str(text or "").lower()
    spans = [(m.start(), m.end(), m.group(0).strip("'-।॥")) for m in TOKEN.finditer(low)]
    toks = [t for _, _, t in spans]
    found, used = [], set()                      # used: token indexes already taken by a phrase
    for tag in sorted((t for t in lex if " " in t), key=len, reverse=True):
        words = tokens(tag)
        for i in range(len(toks)):
            if any(i + k in used for k in range(len(words))) or not _phrase_at(toks, i, words):
                continue
            a, b = spans[i][0], spans[i + len(words) - 1][1]
            found.append((str(text)[a:b], tag, sorted(lex[tag])))
            used.update(range(i, i + len(words)))
            break
    for i, (a, b, token) in enumerate(spans):
        if i in used:
            continue
        for tag, names in lex.items():
            if " " not in tag and _stem_match(token, tag) and not _verb_at(toks, i, tag) and not _idiom_at(toks, i, tag) \
                    and _context_ok(toks, tag, i):
                found.append((str(text)[a:b], tag, sorted(names)))
                break
    seen, out = set(), []
    for said, tag, names in found:
        if tag not in seen:
            seen.add(tag)
            out.append((said, tag, names))
    return out


def _p_at(item: dict, t) -> dict:
    """An item's parameters at ``t``: its first p with every step up to ``t`` laid over it (the Money v2 craft: a
    thing's label changes on the cue word, so the word is shown from that word on)."""
    p = dict(item.get("p") or {}) if isinstance(item.get("p"), dict) else {}
    if t is not None:
        for st in item.get("steps") or []:
            if isinstance(st, dict) and isinstance(st.get("p"), dict) and st.get("t") is not None and float(st["t"]) <= t:
                p.update(st["p"])
    return p


def _strings(v) -> list:
    if isinstance(v, str):
        return [v]
    if isinstance(v, dict):
        return [s for x in v.values() for s in _strings(x)]
    if isinstance(v, (list, tuple)):
        return [s for x in v for s in _strings(x)]
    return []


def _labels(item: dict, t=None) -> str:
    """Every word written on the thing at ``t``: labels, titles, values, axis names, a graph's line and dot labels."""
    return " ".join(_strings(_p_at(item, t))).lower()


def _things(el: dict, t: float) -> list:
    """(draw name, label words) of every drawn thing an element shows at ``t`` (groups, holds, bubble content)."""
    out = []
    if el.get("draw") and el["draw"] not in ("world", "__person__"):
        out.append((el["draw"], _labels(el, t)))
    for m in el.get("group") or []:
        if isinstance(m, dict):
            out += _things(m, t)
    if el.get("kind") == "person":
        held = None
        for h in el.get("holds") or []:
            if h.get("t") is not None and h["t"] <= t:
                held = h.get("item")
        if isinstance(held, dict):
            out += _things(held, t)
    if el.get("kind") == "bubble" and isinstance(el.get("content"), dict):
        out += _things(el["content"], t)
    return out


def _places(scene: dict, t: float) -> set:
    """The place words of where the scene stands at ``t``: its background and any world item on screen."""
    return _place_view(scene, t)[0]


def _place_view(scene: dict, t: float) -> tuple:
    """(place words, the words written on the place) of where the scene stands at ``t``: its background, any world item
    on screen with its kind, and that world's own sign and spot names (label, signs: "पंप 1;पंप 2")."""
    words, written = set(PLACES.get(scene.get("bg") or "", ())), []
    for el in scene.get("els") or []:
        if el.get("draw") == "world" and _visible(el, t, scene):
            p = _p_at(el, t)
            words |= PLACES.get(p.get("kind") or "", set())
            written += [str(p.get(k)) for k in WORLD_WORD_PARAMS if p.get(k)]
    return words, " ; ".join(written).replace(";", " ; ").lower()


def _place_shows(scene: dict, t: float, tag: str, alt: set) -> bool:
    words, written = _place_view(scene, t)
    if tag in words or any(a in words for a in alt):
        return True
    return bool(written) and (has_word(written, tag) or any(has_word(written, a) for a in alt))


def _visible(el, t, scene) -> bool:
    t0 = el.get("t0") if el.get("t0") is not None else scene["t0"]
    t1 = el.get("t1") if el.get("t1") is not None else scene["t1"]
    return t0 <= t < min(t1, scene["t1"])


def _shown_seconds(spec: dict, t0: float, t1: float, tag: str, names: list) -> float:
    hits = 0
    t = t0
    while t < t1:
        for scene in spec.get("scenes") or []:
            if not (scene["t0"] <= t < scene["t1"]):
                continue
            alt, by = aliases(tag), SHOWN_BY.get(tag)
            vis = [el for el in scene.get("els") or [] if _visible(el, t, scene)]
            if _place_shows(scene, t, tag, alt) or any(name in names or has_word(label, tag) or any(has_word(label, a) for a in alt)
                                               for el in vis for name, label in _things(el, t)) \
                    or (by and any(by(el.get("draw"), _p_at(el, t)) for el in vis if el.get("draw"))):
                hits += 1
                break
        t += STEP
    return hits * STEP


def rows(spec: dict, T, only=None) -> list:
    """Per line (of ``only`` when given: the lines the plan places in scenes): what it names and whether each named
    thing is on screen long enough during the line."""
    lex = lexicon()
    out = []
    for lid in T.line_ids():
        if only is not None and lid not in only:
            continue
        line = T.L(lid)
        t0, t1 = float(line["t0"]), float(line["t1"])
        need = min(MIN_SHOWN, (t1 - t0) / 2)
        named = []
        for said, tag, names in named_things(line.get("sub") or "", lex):
            secs = _shown_seconds(spec, t0, t1, tag, names)
            named.append({"word": said, "tag": tag, "saanche": names, "shown_s": round(secs, 1), "shown": secs + 1e-6 >= need})
        out.append({"line": lid, "t0": round(t0, 2), "t1": round(t1, 2), "named": named,
                    "ok": all(n["shown"] for n in named)})
    return out


def summary(rows_: list) -> dict:
    named = [r for r in rows_ if r["named"]]
    ok = sum(1 for r in named if r["ok"])
    return {"lines": len(rows_), "lines_naming_things": len(named), "lines_shown": ok,
            "said_shown_pct": round(100.0 * ok / len(named), 1) if named else 100.0,
            "target_pct": TARGET * 100,
            "missing": [{"line": r["line"], "word": n["word"], "saanche": n["saanche"]}
                        for r in named for n in r["named"] if not n["shown"]]}


def problems(spec: dict, T, only=None) -> list:
    out = []
    for r in rows(spec, T, only):
        for n in r["named"]:
            if not n["shown"]:
                show = " or ".join(n["saanche"][:3])
                out.append(f"line {r['line']} ({r['t0']:.1f}-{r['t1']:.1f}s) names '{n['word']}' but nothing showing it is on "
                           f"screen during the line ({n['shown_s']:.1f}s): show {show} (or a thing labelled "
                           f"'{n['tag']}') while that line is spoken (dikhaya-bola: jo bola, woh dikhe)")
    return out
