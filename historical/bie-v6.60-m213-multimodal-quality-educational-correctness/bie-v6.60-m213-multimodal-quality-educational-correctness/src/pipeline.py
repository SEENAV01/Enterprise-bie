from modality import modality_score,valid as modality_valid
from correctness import correctness_check,valid as correctness_valid
from objective import objective_coverage,valid as objective_valid
from alignment import alignment_record,valid as alignment_valid
from evaluation import weighted_score,decision
from quality_report import quality_report,passed as report_passed
from remediation_signal import remediation_signal,valid as signal_valid
from provenance import provenance,traceable
from verification import verification,passed

def build_quality_evaluation():
    modalities=[
        modality_score("VISUAL",0.96,0.98,["qa-visual"]),
        modality_score("AUDIO",0.94,0.97,["qa-audio"]),
        modality_score("TEXT",0.98,0.99,["qa-caption"]),
        modality_score("TIMING",0.93,0.96,["qa-sync"]),
        modality_score("CAPTION",0.95,0.98,["qa-caption"])
    ]

    checks=[
        correctness_check("cc1","FACTUAL","lesson-1",0.98,["ev-charge"],
                          "Claims match verified source material."),
        correctness_check("cc2","CONCEPTUAL","scene-3",0.96,["ev-force"],
                          "Visual explanation preserves the intended concept."),
        correctness_check("cc3","VISUAL","asset-force-diagram",0.94,["ev-force"]),
        correctness_check("cc4","TEMPORAL","composition-1",0.93,["qa-sync"]),
        correctness_check("cc5","PEDAGOGICAL","lesson-1",0.92,["objective-1"]),
        correctness_check("cc6","OBJECTIVE_COVERAGE","lesson-1",0.96,["objective-1"])
    ]

    objectives=[
        objective_coverage("objective-1",
            "Explain electric charge and attraction/repulsion.",
            True,0.96,["sc2","sc3"],["ev-charge","ev-force"])
    ]

    alignment=[
        alignment_record("align-1","script:b3","sc2",
                         ["asset-force-equation"],"narr-1",["cap-1"],0.96),
        alignment_record("align-2","script:b4","sc3",
                         ["asset-force-diagram"],"narr-2",["cap-2"],0.95)
    ]

    overall=weighted_score(
        [{"score":x["score"]} for x in modalities],
        [0.25,0.20,0.15,0.15,0.10]
    )
    correctness_score=weighted_score(
        [{"score":x["score"]} for x in checks],
        [0.20,0.20,0.15,0.15,0.15,0.15]
    )
    final_score=(overall*0.45)+(correctness_score*0.35)+(
        objectives[0]["coverage_score"]*0.10)+(
        sum(a["score"] for a in alignment)/len(alignment)*0.10
    )
    final_decision=decision(final_score)

    report=quality_report(
        "quality-1","output://lesson-1.mp4",
        modalities,checks,objectives,alignment,
        final_score,final_decision
    )

    signal=remediation_signal(
        "signal-1",report["report_id"],"LOW",
        ["caption-layer"],
        "Caption confidence below ideal threshold.",
        "REVIEW_CAPTION_TIMING"
    )

    prov=provenance(
        report["report_id"],["output://lesson-1.mp4"],
        ["script-1"],["storyboard-1"],
        ["ev-charge","ev-force"],[signal["signal_id"]]
    )
    verification_record=verification(
        "verify-quality",report["report_id"],"PASS",
        ["ev-charge","ev-force"]
    )

    return {
        "schema_version":"6.60",
        "modality_scores":modalities,
        "correctness_checks":checks,
        "objectives":objectives,
        "alignment_records":alignment,
        "quality_report":report,
        "remediation_signal":signal,
        "provenance":prov,
        "verification":verification_record,
        "quality_gate":{"valid":(
            all(modality_valid(x) for x in modalities)
            and all(correctness_valid(x) for x in checks)
            and all(objective_valid(x) for x in objectives)
            and all(alignment_valid(x) for x in alignment)
            and report["decision"] in {"PASS","REVIEW","FAIL"}
            and signal_valid(signal) and traceable(prov)
            and passed(verification_record)
        ),"errors":[]}
    }
