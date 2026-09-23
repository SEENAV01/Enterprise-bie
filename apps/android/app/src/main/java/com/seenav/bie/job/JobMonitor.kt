package com.seenav.bie.job

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.JobResultResult
import com.seenav.bie.api.JobStatusResult
import java.util.concurrent.atomic.AtomicBoolean

interface JobGateway {
    fun getJobStatus(jobId: String, expectedSourceHash: String): JobStatusResult
    fun getJobResult(jobId: String, expectedSourceHash: String): JobResultResult
}

/** Bounded, cancellable foreground-session monitor. Call from an off-main-thread executor. */
class JobMonitor(
    private val gateway: JobGateway,
    val intervalMillis: Long = 2_000,
    val maxAttempts: Int = 30,
    private val sleeper: (Long) -> Unit = { Thread.sleep(it) },
) {
    init { require(intervalMillis >= 0); require(maxAttempts > 0) }

    private val active = AtomicBoolean(false)
    private val cancelled = AtomicBoolean(false)

    fun cancel() { cancelled.set(true) }

    fun monitor(initial: JobTrackingState, publish: (JobTrackingState) -> Unit = {}): JobTrackingState {
        if (!active.compareAndSet(false, true)) return initial
        var state = initial.polling()
        try {
            if (cancelled.get()) return state
            publish(state)
            repeat(maxAttempts) { attempt ->
                if (cancelled.get()) return state
                state = checkOnce(state, publish)
                if (cancelled.get()) return state
                if (state.stage !in setOf(JobTrackingStage.READY, JobTrackingStage.RUNNING)) return state
                if (attempt < maxAttempts - 1) {
                    try { sleeper(intervalMillis) }
                    catch (_: InterruptedException) {
                        cancelled.set(true)
                        Thread.currentThread().interrupt()
                        return state
                    }
                }
            }
            if (!cancelled.get()) {
                state = state.timedOut()
                publish(state)
            }
            return state
        } finally {
            active.set(false)
        }
    }

    /** One status request, with one result request only after governed success. */
    fun refresh(initial: JobTrackingState, publish: (JobTrackingState) -> Unit = {}): JobTrackingState {
        if (!active.compareAndSet(false, true)) return initial
        return try { checkOnce(initial, publish) } finally { active.set(false) }
    }

    private fun checkOnce(initial: JobTrackingState, publish: (JobTrackingState) -> Unit): JobTrackingState {
        if (cancelled.get()) return initial
        val id = initial.jobId ?: return initial.failed(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
        val hash = initial.sourceHash ?: return initial.failed(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
        val response = gateway.getJobStatus(id, hash)
        if (cancelled.get()) return initial
        if (response.error != null || response.status == null) {
            return initial.failed(response.error ?: ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
                .also(publish)
        }
        val observed = initial.observed(response.status)
        publish(observed)
        if (observed.stage != JobTrackingStage.SUCCEEDED || !observed.resultAvailable || cancelled.get()) {
            return observed
        }
        val result = gateway.getJobResult(id, hash)
        if (cancelled.get()) return observed
        return if (result.error != null || result.result == null) {
            observed.failed(result.error ?: ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH).also(publish)
        } else observed.completed(result.result).also(publish)
    }
}
