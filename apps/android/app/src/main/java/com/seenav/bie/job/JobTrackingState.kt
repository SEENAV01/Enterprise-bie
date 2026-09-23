package com.seenav.bie.job

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ApiJob
import com.seenav.bie.api.ApiJobResult
import com.seenav.bie.api.ApiJobStatus
import com.seenav.bie.api.ApiSafeResultSummary

enum class JobTrackingStage { IDLE, POLLING, READY, RUNNING, SUCCEEDED, FAILED, TIMED_OUT, PAUSED, ERROR }

/** Session-only presentation state. It stores neither response JSON nor PDF text. */
data class JobTrackingState(
    val stage: JobTrackingStage = JobTrackingStage.IDLE,
    val jobId: String? = null,
    val sourceHash: String? = null,
    val status: String? = null,
    val queueState: String? = null,
    val resultAvailable: Boolean = false,
    val safeResultSummary: ApiSafeResultSummary? = null,
    val error: ApiClientErrorCode? = null,
) {
    companion object {
        fun submitted(job: ApiJob) = JobTrackingState(
            JobTrackingStage.POLLING, job.jobId, job.sourceHash, job.status,
            resultAvailable = job.resultAvailable,
        )
    }

    fun polling() = copy(stage = JobTrackingStage.POLLING, error = null)

    fun observed(value: ApiJobStatus): JobTrackingState = copy(
        stage = when (value.status) {
            "READY" -> JobTrackingStage.READY
            "RUNNING" -> JobTrackingStage.RUNNING
            "SUCCEEDED" -> JobTrackingStage.SUCCEEDED
            else -> JobTrackingStage.FAILED
        },
        status = value.status,
        queueState = value.queueState,
        resultAvailable = value.resultAvailable,
        safeResultSummary = null,
        error = if (value.status == "FAILED") ApiClientErrorCode.JOB_FAILED else null,
    )

    fun completed(value: ApiJobResult) = copy(
        stage = JobTrackingStage.SUCCEEDED,
        safeResultSummary = value.summary,
        error = null,
    )

    fun timedOut() = copy(stage = JobTrackingStage.TIMED_OUT, error = ApiClientErrorCode.POLLING_TIMEOUT)
    fun paused() = copy(stage = JobTrackingStage.PAUSED, error = null)
    fun failed(code: ApiClientErrorCode) = copy(
        stage = JobTrackingStage.ERROR, safeResultSummary = null, error = code,
    )
}
