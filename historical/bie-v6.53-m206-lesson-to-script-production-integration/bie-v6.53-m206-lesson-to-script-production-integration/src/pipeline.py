from lesson_input import lesson_input,valid as lesson_valid
from script_blocks import block,valid as block_valid
from script import script,valid as script_valid
from coverage import coverage,complete
from timing import timing,within_target
from evidence import evidence_check,all_grounded
from provenance import provenance,traceable
from verification import verification,passed

def build_lesson_to_script():
    lesson=lesson_input(
        "lesson-1","Charge to Electric Force",
        ["obj-charge","obj-force"],["c-charge"],12,
        ["ev-charge","ev-force"]
    )

    blocks=[
        block("b1","HOOK","Why does electric charge create force?",
              ["obj-charge"],["ev-charge"],1,20),
        block("b2","OBJECTIVE","We will explain charge and predict force direction.",
              ["obj-charge","obj-force"],["ev-charge","ev-force"],2,25),
        block("b3","EXPLANATION","Electric charge is a conserved and quantized property.",
              ["obj-charge"],["ev-charge"],3,55),
        block("b4","DEMONSTRATION","Like charges repel and unlike charges attract.",
              ["obj-force"],["ev-force"],4,50),
        block("b5","CHECK_FOR_UNDERSTANDING",
              "Which direction should the force point in this case?",
              ["obj-force"],["ev-force"],5,35),
        block("b6","SUMMARY","Charge is the foundation; force describes its interaction.",
              ["obj-charge","obj-force"],["ev-charge","ev-force"],6,35)
    ]

    scr=script("script-1",lesson["lesson_id"],blocks,
               "clear","learner",220)
    cov=coverage(lesson["objectives"],scr["blocks"])
    tm=timing(scr["blocks"])
    ev=evidence_check(scr["blocks"])
    prov=provenance(scr["script_id"],[lesson["lesson_id"]],
                    lesson["objectives"],lesson["evidence_ids"],
                    ["artifact://lesson-plan"])
    check=verification("verify-1","script-1","PASS",
                       lesson["evidence_ids"])

    return {
        "schema_version":"6.53","lesson":lesson,"script":scr,
        "coverage":cov,"timing":tm,"evidence_checks":ev,
        "provenance":prov,"verification":check,
        "quality_gate":{"valid":(
            lesson_valid(lesson) and
            all(block_valid(b) for b in blocks) and
            script_valid(scr) and complete(cov) and
            within_target(tm,scr["target_duration_sec"]) and
            all_grounded(ev) and traceable(prov) and passed(check)
        ),"errors":[]}
    }
