package com.seenav.bie.job

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ApiJob
import com.seenav.bie.api.ApiJobResult
import com.seenav.bie.api.ApiJobStatus
import com.seenav.bie.api.ApiSafeResultSummary
import com.seenav.bie.api.JobResultResult
import com.seenav.bie.api.JobStatusResult
import org.junit.Assert.*
import org.junit.Test

class JobMonitorTest {
    private val id = "job-" + "a".repeat(64)
    private val hash = "b".repeat(64)
    private val initial = JobTrackingState.submitted(ApiJob(id, "READY", hash, false))
    private val safe = ApiSafeResultSummary(hash, 123, 2, 4, "hierarchy_v1", "toc_v1",
        1, 1, 0, 0, 0, 0, 0, 0, 0, 0, "no_native_outline")

    private fun status(stage: String, queue: String = "DELIVERED") = ApiJobStatus(
        id, stage, hash, stage == "SUCCEEDED", queue,
    )

    private class FakeGateway(
        val statuses: MutableList<JobStatusResult>,
        var result: JobResultResult,
    ) : JobGateway {
        var statusCalls = 0
        var resultCalls = 0
        var onStatus: (() -> Unit)? = null
        override fun getJobStatus(jobId: String, expectedSourceHash: String): JobStatusResult {
            statusCalls++
            onStatus?.invoke()
            return if (statuses.isNotEmpty()) statuses.removeAt(0)
                else JobStatusResult(error = ApiClientErrorCode.NETWORK_UNAVAILABLE)
        }
        override fun getJobResult(jobId: String, expectedSourceHash: String): JobResultResult {
            resultCalls++
            return result
        }
    }

    private fun gateway(vararg statuses: ApiJobStatus) = FakeGateway(
        statuses.map { JobStatusResult(status = it) }.toMutableList(),
        JobResultResult(result = ApiJobResult(id, safe)),
    )

    @Test fun readyReadyRunningSucceededCompletes() {
        val fake = gateway(status("READY"), status("READY"), status("RUNNING"), status("SUCCEEDED"))
        val seen = mutableListOf<JobTrackingStage>()
        val ended = JobMonitor(fake, 0, 4) {}.monitor(initial) { seen.add(it.stage) }
        assertEquals(JobTrackingStage.SUCCEEDED, ended.stage)
        assertEquals(listOf(JobTrackingStage.POLLING, JobTrackingStage.READY, JobTrackingStage.READY,
            JobTrackingStage.RUNNING, JobTrackingStage.SUCCEEDED, JobTrackingStage.SUCCEEDED), seen)
    }
    @Test fun resultNotFetchedWhilePending() {
        val fake = gateway(status("READY"), status("RUNNING"))
        JobMonitor(fake, 0, 2) {}.monitor(initial)
        assertEquals(0, fake.resultCalls)
    }
    @Test fun resultFetchedOnceOnSuccess() {
        val fake = gateway(status("READY"), status("SUCCEEDED"))
        JobMonitor(fake, 0, 3) {}.monitor(initial)
        assertEquals(1, fake.resultCalls)
    }
    @Test fun failedStopsImmediately() {
        val fake = gateway(status("FAILED"), status("READY"))
        val ended = JobMonitor(fake, 0, 3) {}.monitor(initial)
        assertEquals(JobTrackingStage.FAILED, ended.stage)
        assertEquals(1, fake.statusCalls)
    }
    @Test fun failedDoesNotFetchResult() {
        val fake = gateway(status("FAILED"))
        JobMonitor(fake, 0, 3) {}.monitor(initial)
        assertEquals(0, fake.resultCalls)
    }
    @Test fun exactAttemptLimit() {
        val fake = gateway(status("READY"), status("READY"), status("READY"), status("READY"))
        JobMonitor(fake, 0, 3) {}.monitor(initial)
        assertEquals(3, fake.statusCalls)
    }
    @Test fun timeoutIsNotJobFailure() {
        val fake = gateway(status("RUNNING"))
        val ended = JobMonitor(fake, 0, 1) {}.monitor(initial)
        assertEquals(JobTrackingStage.TIMED_OUT, ended.stage)
        assertEquals(ApiClientErrorCode.POLLING_TIMEOUT, ended.error)
        assertEquals(id, ended.jobId)
    }
    @Test fun networkFailureRetainsIdentity() {
        val fake = gateway()
        val ended = JobMonitor(fake, 0, 1) {}.monitor(initial)
        assertEquals(JobTrackingStage.ERROR, ended.stage)
        assertEquals(id, ended.jobId)
        assertEquals(hash, ended.sourceHash)
    }
    @Test fun cancellationStopsRequests() {
        val fake = gateway(status("READY"), status("SUCCEEDED"))
        lateinit var monitor: JobMonitor
        monitor = JobMonitor(fake, 0, 3) { monitor.cancel() }
        monitor.monitor(initial)
        assertEquals(1, fake.statusCalls)
        assertEquals(0, fake.resultCalls)
    }
    @Test fun replacementCancelsOldMonitor() {
        val old = gateway(status("READY"), status("SUCCEEDED"))
        lateinit var oldMonitor: JobMonitor
        oldMonitor = JobMonitor(old, 0, 3) { oldMonitor.cancel() }
        oldMonitor.monitor(initial)
        val replacement = gateway(status("SUCCEEDED"))
        val next = initial.copy(jobId = "job-" + "c".repeat(64))
        JobMonitor(replacement, 0, 1) {}.monitor(next)
        assertEquals(1, old.statusCalls)
        assertEquals(1, replacement.statusCalls)
    }
    @Test fun refreshAfterTimeoutReadsOnce() {
        val fake = gateway(status("READY"), status("RUNNING"))
        val monitor = JobMonitor(fake, 0, 1) {}
        val timedOut = monitor.monitor(initial)
        val refreshed = monitor.refresh(timedOut)
        assertEquals(JobTrackingStage.RUNNING, refreshed.stage)
        assertEquals(2, fake.statusCalls)
    }
    @Test fun refreshSucceededFetchesResult() {
        val fake = gateway(status("SUCCEEDED"))
        val ended = JobMonitor(fake, 0, 1) {}.refresh(initial)
        assertEquals(safe, ended.safeResultSummary)
        assertEquals(1, fake.resultCalls)
    }
    @Test fun duplicateStartDoesNotCreateSecondPoller() {
        val fake = gateway(status("READY"))
        lateinit var monitor: JobMonitor
        var nested: JobTrackingState? = null
        monitor = JobMonitor(fake, 0, 1) {}
        fake.onStatus = { nested = monitor.monitor(initial) }
        monitor.monitor(initial)
        assertEquals(initial, nested)
        assertEquals(1, fake.statusCalls)
    }
    @Test fun refreshDoesNotCreateConcurrentPoller() {
        val fake = gateway(status("READY"))
        lateinit var monitor: JobMonitor
        var nested: JobTrackingState? = null
        monitor = JobMonitor(fake, 0, 1) {}
        fake.onStatus = { nested = monitor.refresh(initial) }
        monitor.monitor(initial)
        assertEquals(initial, nested)
        assertEquals(1, fake.statusCalls)
    }
}
