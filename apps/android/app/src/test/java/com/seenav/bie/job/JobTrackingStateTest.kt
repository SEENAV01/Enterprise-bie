package com.seenav.bie.job

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ApiJob
import com.seenav.bie.api.ApiJobResult
import com.seenav.bie.api.ApiJobStatus
import com.seenav.bie.api.ApiSafeResultSummary
import org.junit.Assert.*
import org.junit.Test

class JobTrackingStateTest {
    private val id = "job-" + "a".repeat(64)
    private val hash = "b".repeat(64)
    private val submitted = JobTrackingState.submitted(ApiJob(id, "READY", hash, false))
    private val safe = ApiSafeResultSummary(hash, 123, 2, 4, "hierarchy_v1", "toc_v1",
        1, 1, 0, 0, 0, 0, 0, 0, 0, 0, "no_native_outline")
    private fun observed(stage: String) = submitted.observed(ApiJobStatus(id, stage, hash,
        stage == "SUCCEEDED", if (stage == "FAILED") "DEAD_LETTER" else "DELIVERED"))

    @Test fun submittedEntersMonitoring() { assertEquals(JobTrackingStage.POLLING, submitted.stage) }
    @Test fun readyIsTruthful() { assertEquals(JobTrackingStage.READY, observed("READY").stage) }
    @Test fun runningIsTruthful() { assertEquals(JobTrackingStage.RUNNING, observed("RUNNING").stage) }
    @Test fun successStoresOnlySafeSummary() { assertEquals(safe, observed("SUCCEEDED").completed(ApiJobResult(id, safe)).safeResultSummary) }
    @Test fun failedStoresNoResult() { assertNull(observed("FAILED").safeResultSummary) }
    @Test fun timeoutRetainsJobId() { assertEquals(id, submitted.timedOut().jobId) }
    @Test fun foregroundPauseRetainsIdentityWithoutTimeoutError() { val paused = submitted.paused(); assertEquals(id, paused.jobId); assertNull(paused.error) }
    @Test fun safeSummaryHasCountsAndNoText() { assertFalse(safe.toString().contains("book passage")); assertEquals(2, safe.pageCount) }
    @Test fun replacementClearsOldResult() {
        val old = observed("SUCCEEDED").completed(ApiJobResult(id, safe))
        val replacement = JobTrackingState.submitted(ApiJob("job-" + "c".repeat(64), "READY", hash, false))
        assertNotEquals(old.jobId, replacement.jobId)
        assertNull(replacement.safeResultSummary)
    }
    @Test fun failedStatusUsesSafeCode() { assertEquals(ApiClientErrorCode.JOB_FAILED, observed("FAILED").error) }
}
