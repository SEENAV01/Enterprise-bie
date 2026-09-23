package com.seenav.bie.api

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.contentOrNull
import kotlinx.serialization.json.longOrNull

internal const val EXPECTED_HEALTH_STATUS = "ok"
internal const val EXPECTED_SERVICE = "bie-api"
internal const val EXPECTED_API_VERSION = "v1"
internal const val EXPECTED_DOCUMENT_INSPECTION = "native_pdf_toc_v1"
internal const val EXPECTED_PERSISTENCE_BACKEND = "local_sqlite_cas_v1"
internal const val EXPECTED_WORKER_MODE = "local_manual_run_once_v1"

data class ApiHealth(val status: String, val service: String, val apiVersion: String) {
    fun matchesContract(): Boolean = status == EXPECTED_HEALTH_STATUS &&
        service == EXPECTED_SERVICE && apiVersion == EXPECTED_API_VERSION
}

data class ApiCapabilities(
    val apiVersion: String,
    val documentInspection: String,
    val stateless: Boolean,
    val persistence: Boolean,
    val asyncJobs: Boolean,
    val authentication: Boolean,
    val productAccepted: Boolean,
    val persistenceBackend: String,
    val workerMode: String,
) {
    fun matchesContract(): Boolean = apiVersion == EXPECTED_API_VERSION &&
        documentInspection == EXPECTED_DOCUMENT_INSPECTION && !stateless && persistence &&
        asyncJobs && !authentication && !productAccepted &&
        persistenceBackend == EXPECTED_PERSISTENCE_BACKEND && workerMode == EXPECTED_WORKER_MODE
}

data class ApiJob(val jobId: String, val status: String, val sourceHash: String, val resultAvailable: Boolean)

data class ApiJobSubmission(val apiSchemaVersion: String, val job: ApiJob) {
    fun matchesContract(): Boolean = apiSchemaVersion == "1.0" &&
        Regex("job-[0-9a-f]{64}").matches(job.jobId) &&
        Regex("[0-9a-f]{64}").matches(job.sourceHash) &&
        job.status in setOf("READY", "RUNNING", "SUCCEEDED", "FAILED") &&
        job.resultAvailable == (job.status == "SUCCEEDED")
}

internal val JOB_ID_PATTERN = Regex("job-[0-9a-f]{64}")
internal val SOURCE_HASH_PATTERN = Regex("[0-9a-f]{64}")

data class ApiJobStatus(
    val jobId: String,
    val status: String,
    val sourceHash: String,
    val resultAvailable: Boolean,
    val queueState: String,
) {
    fun matchesContract(): Boolean = JOB_ID_PATTERN.matches(jobId) &&
        SOURCE_HASH_PATTERN.matches(sourceHash) &&
        status in setOf("READY", "RUNNING", "SUCCEEDED", "FAILED") &&
        queueState in setOf("READY", "DELIVERED", "ACKED", "DEAD_LETTER") &&
        resultAvailable == (status == "SUCCEEDED") &&
        when (status) {
            "READY" -> queueState in setOf("READY", "DELIVERED")
            "RUNNING" -> queueState == "DELIVERED"
            "SUCCEEDED" -> queueState in setOf("DELIVERED", "ACKED")
            "FAILED" -> queueState in setOf("DELIVERED", "DEAD_LETTER")
            else -> false
        }
}

/** Only governed counts and policy identifiers are retained; no document text is parsed. */
data class ApiSafeResultSummary(
    val sourceHash: String,
    val byteLength: Long,
    val pageCount: Int,
    val totalBlocks: Int,
    val hierarchyPolicy: String,
    val tocReconciliationPolicy: String,
    val headingCandidateCount: Int,
    val materializedChapterCount: Int,
    val materializedSectionCount: Int,
    val materializedSubsectionCount: Int,
    val nativeOutlineEntryCount: Int,
    val outlineResolvablePageCount: Int,
    val reconciliationMatchCount: Int,
    val unmatchedOutlineCount: Int,
    val ambiguousDetectedTitleCount: Int,
    val exactPageMatchCount: Int,
    val outlineStatus: String,
) {
    fun matchesContract(): Boolean = SOURCE_HASH_PATTERN.matches(sourceHash) && byteLength > 0 &&
        pageCount >= 1 && hierarchyPolicy.isNotBlank() && tocReconciliationPolicy.isNotBlank() &&
        listOf(totalBlocks, headingCandidateCount, materializedChapterCount,
            materializedSectionCount, materializedSubsectionCount, nativeOutlineEntryCount,
            outlineResolvablePageCount, reconciliationMatchCount, unmatchedOutlineCount,
            ambiguousDetectedTitleCount, exactPageMatchCount).all { it >= 0 } &&
        outlineStatus in setOf("no_native_outline", "native_outline_reconciled")
}

data class ApiJobResult(val jobId: String, val summary: ApiSafeResultSummary)

internal class InvalidApiJson : Exception()

internal object ApiJson {
    private val json = Json { ignoreUnknownKeys = true }

    fun health(body: String): ApiHealth {
        val fields = objectFields(body)
        return ApiHealth(
            fields.requiredString("status"),
            fields.requiredString("service"),
            fields.requiredString("api_version"),
        )
    }

    fun capabilities(body: String): ApiCapabilities {
        val fields = objectFields(body)
        return ApiCapabilities(
            apiVersion = fields.requiredString("api_version"),
            documentInspection = fields.requiredString("document_inspection"),
            stateless = fields.requiredBoolean("stateless"),
            persistence = fields.requiredBoolean("persistence"),
            asyncJobs = fields.requiredBoolean("async_jobs"),
            authentication = fields.requiredBoolean("authentication"),
            productAccepted = fields.requiredBoolean("product_accepted"),
            persistenceBackend = fields.requiredString("persistence_backend"),
            workerMode = fields.requiredString("worker_mode"),
        )
    }

    fun jobSubmission(body: String): ApiJobSubmission {
        val fields = objectFields(body)
        val job = fields["job"] as? JsonObject ?: throw InvalidApiJson()
        return ApiJobSubmission(
            apiSchemaVersion = fields.requiredString("api_schema_version"),
            job = ApiJob(job.requiredString("job_id"), job.requiredString("status"),
                job.requiredString("source_hash"), job.requiredBoolean("result_available")),
        )
    }

    fun jobStatus(body: String): ApiJobStatus {
        val fields = objectFields(body)
        if (fields.requiredString("api_schema_version") != "1.0") throw InvalidApiJson()
        val job = fields["job"] as? JsonObject ?: throw InvalidApiJson()
        return ApiJobStatus(
            job.requiredString("job_id"), job.requiredString("status"),
            job.requiredString("source_hash"), job.requiredBoolean("result_available"),
            job.requiredString("queue_state"),
        )
    }

    fun jobResult(body: String): ApiJobResult {
        val fields = objectFields(body)
        if (fields.requiredString("api_schema_version") != "1.0") throw InvalidApiJson()
        val result = fields["result"] as? JsonObject ?: throw InvalidApiJson()
        return ApiJobResult(fields.requiredString("job_id"), ApiSafeResultSummary(
            sourceHash = result.requiredString("source_hash"),
            byteLength = result.requiredLong("byte_length"),
            pageCount = result.requiredInt("page_count"),
            totalBlocks = result.requiredInt("total_blocks"),
            hierarchyPolicy = result.requiredString("hierarchy_policy"),
            tocReconciliationPolicy = result.requiredString("toc_reconciliation_policy"),
            headingCandidateCount = result.requiredInt("heading_candidate_count"),
            materializedChapterCount = result.requiredInt("materialized_chapter_count"),
            materializedSectionCount = result.requiredInt("materialized_section_count"),
            materializedSubsectionCount = result.requiredInt("materialized_subsection_count"),
            nativeOutlineEntryCount = result.requiredInt("native_outline_entry_count"),
            outlineResolvablePageCount = result.requiredInt("outline_resolvable_page_count"),
            reconciliationMatchCount = result.requiredInt("reconciliation_match_count"),
            unmatchedOutlineCount = result.requiredInt("unmatched_outline_count"),
            ambiguousDetectedTitleCount = result.requiredInt("ambiguous_detected_title_count"),
            exactPageMatchCount = result.requiredInt("exact_page_match_count"),
            outlineStatus = result.requiredString("outline_status"),
        ))
    }

    fun governedErrorCode(body: String): String {
        val error = objectFields(body)["error"] as? JsonObject ?: throw InvalidApiJson()
        return error.requiredString("code")
    }

    private fun objectFields(body: String): JsonObject = try {
        json.parseToJsonElement(body).jsonObject
    } catch (_: Exception) {
        throw InvalidApiJson()
    }

    private fun JsonObject.requiredString(name: String): String {
        val value = this[name] as? JsonPrimitive ?: throw InvalidApiJson()
        if (!value.isString) throw InvalidApiJson()
        return value.contentOrNull ?: throw InvalidApiJson()
    }

    private fun JsonObject.requiredBoolean(name: String): Boolean {
        val value = this[name] as? JsonPrimitive ?: throw InvalidApiJson()
        return value.booleanOrNull ?: throw InvalidApiJson()
    }

    private fun JsonObject.requiredLong(name: String): Long {
        val value = this[name] as? JsonPrimitive ?: throw InvalidApiJson()
        if (value.isString) throw InvalidApiJson()
        return value.longOrNull ?: throw InvalidApiJson()
    }

    private fun JsonObject.requiredInt(name: String): Int {
        val value = requiredLong(name)
        if (value < Int.MIN_VALUE || value > Int.MAX_VALUE) throw InvalidApiJson()
        return value.toInt()
    }
}
