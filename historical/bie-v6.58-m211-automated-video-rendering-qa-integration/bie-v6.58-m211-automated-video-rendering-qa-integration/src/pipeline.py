from render_job import render_job,valid as job_valid
from renderer_adapter import renderer_adapter,valid as adapter_valid
from render_result import render_result,successful
from qa_checks import qa_check,passed as check_passed
from qa_report import qa_report,passed as report_passed
from retry import retry_policy,should_retry
from manifest import output_manifest,valid as manifest_valid
from provenance import provenance,traceable
from verification import verification,passed

def build_render_qa_integration():
    adapter=renderer_adapter(
        "renderer-1","Remotion","6.x",
        ["composition","audio","captions","frame-render"]
    )
    job=render_job(
        "job-1","composition-1","render-1080p",
        "output://lesson-1.mp4"
    )

    result=render_result(
        job["job_id"],"SUCCEEDED","output://lesson-1.mp4",
        195,5850,24000000,"sha256:example"
    )

    checks=[
        qa_check("qa1","FILE_EXISTS",result["output_path"],True,True),
        qa_check("qa2","DURATION",result["output_path"],195,195),
        qa_check("qa3","FRAME_COUNT",result["output_path"],5850,5850),
        qa_check("qa4","RESOLUTION",result["output_path"],
                 "1920x1080","1920x1080"),
        qa_check("qa5","FPS",result["output_path"],30,30),
        qa_check("qa6","AUDIO_PRESENT",result["output_path"],True,True),
        qa_check("qa7","AUDIO_SYNC",result["output_path"],True,True),
        qa_check("qa8","CAPTION_SYNC",result["output_path"],True,True),
        qa_check("qa9","SCENE_COVERAGE",result["output_path"],True,True),
        qa_check("qa10","BLACK_FRAMES",result["output_path"],0,0),
        qa_check("qa11","FREEZE_FRAMES",result["output_path"],0,0),
        qa_check("qa12","CORRUPTION",result["output_path"],False,False),
        qa_check("qa13","CHECKSUM",result["output_path"],
                 "sha256:example","sha256:example")
    ]

    report=qa_report("report-1",job["job_id"],checks,"PASS",
                     ["output://lesson-1.mp4"])
    retry=retry_policy()
    manifest=output_manifest(
        job["job_id"],
        [{"path":result["output_path"],"format":"MP4",
          "checksum":result["checksum"]}],
        result["output_path"]
    )
    prov=provenance(
        job["job_id"],["composition-1"],["render-1080p"],["report-1"],
        ["artifact://video-composition"]
    )
    verification_record=verification(
        "verify-render","job-1","PASS"
    )

    return {
        "schema_version":"6.58",
        "renderer_adapter":adapter,
        "render_job":job,
        "render_result":result,
        "qa_report":report,
        "retry_policy":retry,
        "output_manifest":manifest,
        "provenance":prov,
        "verification":verification_record,
        "quality_gate":{"valid":(
            adapter_valid(adapter)
            and job_valid(job)
            and successful(result)
            and report_passed(report)
            and manifest_valid(manifest)
            and traceable(prov)
            and passed(verification_record)
        ),"errors":[]}
    }
