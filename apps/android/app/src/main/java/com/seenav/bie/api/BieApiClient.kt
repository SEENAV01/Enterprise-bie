package com.seenav.bie.api

import java.io.ByteArrayOutputStream
import java.io.IOException
import java.io.FileInputStream
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets
import com.seenav.bie.document.PreparedPdf
import com.seenav.bie.document.MAX_PDF_BYTES
import com.seenav.bie.job.JobGateway

enum class ApiClientErrorCode {
    API_NOT_CONFIGURED,
    INVALID_API_BASE_URL,
    NETWORK_UNAVAILABLE,
    HTTP_ERROR,
    RESPONSE_TOO_LARGE,
    INVALID_CONTENT_TYPE,
    INVALID_JSON,
    HEALTH_CONTRACT_MISMATCH,
    CAPABILITY_CONTRACT_MISMATCH,
    INTERNAL_CLIENT_ERROR,
    INVALID_DOCUMENT_TYPE,
    EMPTY_DOCUMENT,
    DOCUMENT_TOO_LARGE,
    DOCUMENT_READ_FAILED,
    IDEMPOTENCY_CONFLICT,
    SUBMISSION_CONTRACT_MISMATCH,
    SOURCE_HASH_MISMATCH,
    JOB_NOT_FOUND,
    JOB_STATUS_CONTRACT_MISMATCH,
    JOB_RESULT_CONTRACT_MISMATCH,
    JOB_ID_MISMATCH,
    JOB_FAILED,
    RESULT_NOT_READY,
    POLLING_TIMEOUT,
}

data class JobStatusResult(val status: ApiJobStatus? = null, val error: ApiClientErrorCode? = null)
data class JobResultResult(val result: ApiJobResult? = null, val error: ApiClientErrorCode? = null)

data class SubmissionResult(val job: ApiJob? = null, val error: ApiClientErrorCode? = null) {
    companion object {
        fun failed(code: ApiClientErrorCode) = SubmissionResult(error = code)
    }
}

data class ConnectionCheckResult(
    val backendConnected: Boolean,
    val documentIntelligenceConnected: Boolean,
    val error: ApiClientErrorCode? = null,
) {
    companion object {
        fun failed(code: ApiClientErrorCode) = ConnectionCheckResult(false, false, code)
        fun connected() = ConnectionCheckResult(true, true)
    }
}

class BieApiClient(
    private val config: BieApiConfig,
    private val connectTimeoutMillis: Int = 5_000,
    private val readTimeoutMillis: Int = 10_000,
    private val maximumResponseBytes: Int = 256 * 1024,
) : JobGateway {
    override fun getJobStatus(jobId: String, expectedSourceHash: String): JobStatusResult {
        if (!JOB_ID_PATTERN.matches(jobId) || !SOURCE_HASH_PATTERN.matches(expectedSourceHash)) {
            return JobStatusResult(error = ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
        }
        config.error?.let { return JobStatusResult(error = it) }
        val base = config.baseUrl ?: return JobStatusResult(error = ApiClientErrorCode.API_NOT_CONFIGURED)
        return try {
            val response = getJobHttp(base, "/v1/jobs/$jobId")
            if (response.status == 404) return JobStatusResult(error = ApiClientErrorCode.JOB_NOT_FOUND)
            if (response.status != 200) return JobStatusResult(error = ApiClientErrorCode.HTTP_ERROR)
            val status = ApiJson.jobStatus(response.body ?: throw InvalidApiJson())
            when {
                !status.matchesContract() -> JobStatusResult(error = ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
                status.jobId != jobId -> JobStatusResult(error = ApiClientErrorCode.JOB_ID_MISMATCH)
                status.sourceHash != expectedSourceHash -> JobStatusResult(error = ApiClientErrorCode.SOURCE_HASH_MISMATCH)
                else -> JobStatusResult(status = status)
            }
        } catch (error: SafeClientFailure) {
            JobStatusResult(error = error.code)
        } catch (_: InvalidApiJson) {
            JobStatusResult(error = ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH)
        } catch (_: IOException) {
            JobStatusResult(error = ApiClientErrorCode.NETWORK_UNAVAILABLE)
        } catch (_: Exception) {
            JobStatusResult(error = ApiClientErrorCode.INTERNAL_CLIENT_ERROR)
        }
    }

    override fun getJobResult(jobId: String, expectedSourceHash: String): JobResultResult {
        if (!JOB_ID_PATTERN.matches(jobId) || !SOURCE_HASH_PATTERN.matches(expectedSourceHash)) {
            return JobResultResult(error = ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH)
        }
        config.error?.let { return JobResultResult(error = it) }
        val base = config.baseUrl ?: return JobResultResult(error = ApiClientErrorCode.API_NOT_CONFIGURED)
        return try {
            val response = getJobHttp(base, "/v1/jobs/$jobId/result")
            if (response.status == 404) return JobResultResult(error = ApiClientErrorCode.JOB_NOT_FOUND)
            if (response.status == 409) {
                val code = try { ApiJson.governedErrorCode(response.body ?: "") }
                    catch (_: InvalidApiJson) { "" }
                return JobResultResult(error = when (code) {
                    "result_not_ready" -> ApiClientErrorCode.RESULT_NOT_READY
                    "job_failed" -> ApiClientErrorCode.JOB_FAILED
                    else -> ApiClientErrorCode.HTTP_ERROR
                })
            }
            if (response.status != 200) return JobResultResult(error = ApiClientErrorCode.HTTP_ERROR)
            val result = ApiJson.jobResult(response.body ?: throw InvalidApiJson())
            when {
                !JOB_ID_PATTERN.matches(result.jobId) || !result.summary.matchesContract() ->
                    JobResultResult(error = ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH)
                result.jobId != jobId -> JobResultResult(error = ApiClientErrorCode.JOB_ID_MISMATCH)
                result.summary.sourceHash != expectedSourceHash ->
                    JobResultResult(error = ApiClientErrorCode.SOURCE_HASH_MISMATCH)
                else -> JobResultResult(result = result)
            }
        } catch (error: SafeClientFailure) {
            JobResultResult(error = error.code)
        } catch (_: InvalidApiJson) {
            JobResultResult(error = ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH)
        } catch (_: IOException) {
            JobResultResult(error = ApiClientErrorCode.NETWORK_UNAVAILABLE)
        } catch (_: Exception) {
            JobResultResult(error = ApiClientErrorCode.INTERNAL_CLIENT_ERROR)
        }
    }

    private data class JobHttpResponse(val status: Int, val body: String? = null)

    private fun getJobHttp(base: String, path: String): JobHttpResponse {
        val connection = URL(base + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "GET"
            connection.connectTimeout = connectTimeoutMillis
            connection.readTimeout = readTimeoutMillis
            connection.instanceFollowRedirects = false
            connection.setRequestProperty("Accept", "application/json")
            val status = connection.responseCode
            val body = when (status) {
                200 -> readJson(connection)
                409 -> try { readJson(connection, errorStream = true) }
                    catch (_: SafeClientFailure) { null }
                else -> null
            }
            return JobHttpResponse(status, body)
        } finally {
            connection.disconnect()
        }
    }
    fun submitDocument(prepared: PreparedPdf): SubmissionResult {
        config.error?.let { return SubmissionResult.failed(it) }
        val base = config.baseUrl ?: return SubmissionResult.failed(ApiClientErrorCode.API_NOT_CONFIGURED)
        if (prepared.byteLength > MAX_PDF_BYTES) return SubmissionResult.failed(ApiClientErrorCode.DOCUMENT_TOO_LARGE)
        if (prepared.byteLength <= 0L || !prepared.cacheFile.isFile ||
            prepared.cacheFile.length() != prepared.byteLength
        ) return SubmissionResult.failed(ApiClientErrorCode.DOCUMENT_READ_FAILED)
        return try {
            val body = postPdf(base, prepared)
            val response = ApiJson.jobSubmission(body)
            if (!response.matchesContract()) SubmissionResult.failed(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH)
            else if (response.job.sourceHash != prepared.sourceSha256) {
                SubmissionResult.failed(ApiClientErrorCode.SOURCE_HASH_MISMATCH)
            } else SubmissionResult(job = response.job)
        } catch (error: SafeClientFailure) {
            SubmissionResult.failed(error.code)
        } catch (_: InvalidApiJson) {
            SubmissionResult.failed(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH)
        } catch (_: IOException) {
            SubmissionResult.failed(ApiClientErrorCode.NETWORK_UNAVAILABLE)
        } catch (_: Exception) {
            SubmissionResult.failed(ApiClientErrorCode.INTERNAL_CLIENT_ERROR)
        }
    }

    private fun postPdf(base: String, prepared: PreparedPdf): String {
        val connection = URL(base + "/v1/jobs/document-inspection").openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "POST"
            connection.connectTimeout = connectTimeoutMillis
            connection.readTimeout = readTimeoutMillis
            connection.instanceFollowRedirects = false
            connection.doOutput = true
            connection.setRequestProperty("Content-Type", "application/pdf")
            connection.setRequestProperty("Accept", "application/json")
            connection.setRequestProperty("Idempotency-Key", prepared.idempotencyKey)
            connection.setFixedLengthStreamingMode(prepared.byteLength)
            FileInputStream(prepared.cacheFile).use { input ->
                connection.outputStream.use { output ->
                    val buffer = ByteArray(8 * 1024)
                    var sent = 0L
                    while (true) {
                        val count = input.read(buffer)
                        if (count < 0) break
                        sent += count
                        if (sent > prepared.byteLength) throw SafeClientFailure(ApiClientErrorCode.DOCUMENT_READ_FAILED)
                        output.write(buffer, 0, count)
                    }
                    if (sent != prepared.byteLength) throw SafeClientFailure(ApiClientErrorCode.DOCUMENT_READ_FAILED)
                }
            }
            return when (connection.responseCode) {
                202 -> readJson(connection)
                409 -> throw SafeClientFailure(ApiClientErrorCode.IDEMPOTENCY_CONFLICT)
                413 -> throw SafeClientFailure(ApiClientErrorCode.DOCUMENT_TOO_LARGE)
                else -> throw SafeClientFailure(ApiClientErrorCode.HTTP_ERROR)
            }
        } finally {
            connection.disconnect()
        }
    }
    fun checkConnection(): ConnectionCheckResult {
        config.error?.let { return ConnectionCheckResult.failed(it) }
        val base = config.baseUrl ?: return ConnectionCheckResult.failed(ApiClientErrorCode.API_NOT_CONFIGURED)
        return try {
            val health = ApiJson.health(getJson(base, "/healthz"))
            if (!health.matchesContract()) {
                return ConnectionCheckResult.failed(ApiClientErrorCode.HEALTH_CONTRACT_MISMATCH)
            }
            val capabilities = ApiJson.capabilities(getJson(base, "/v1/capabilities"))
            if (!capabilities.matchesContract()) {
                return ConnectionCheckResult.failed(ApiClientErrorCode.CAPABILITY_CONTRACT_MISMATCH)
            }
            ConnectionCheckResult.connected()
        } catch (error: SafeClientFailure) {
            ConnectionCheckResult.failed(error.code)
        } catch (_: InvalidApiJson) {
            ConnectionCheckResult.failed(ApiClientErrorCode.INVALID_JSON)
        } catch (_: IOException) {
            ConnectionCheckResult.failed(ApiClientErrorCode.NETWORK_UNAVAILABLE)
        } catch (_: Exception) {
            ConnectionCheckResult.failed(ApiClientErrorCode.INTERNAL_CLIENT_ERROR)
        }
    }

    private fun getJson(base: String, path: String): String {
        val connection = URL(base + path).openConnection() as HttpURLConnection
        try {
            connection.requestMethod = "GET"
            connection.connectTimeout = connectTimeoutMillis
            connection.readTimeout = readTimeoutMillis
            connection.instanceFollowRedirects = false
            connection.setRequestProperty("Accept", "application/json")
            if (connection.responseCode != HttpURLConnection.HTTP_OK) {
                throw SafeClientFailure(ApiClientErrorCode.HTTP_ERROR)
            }
            return readJson(connection)
        } finally {
            connection.disconnect()
        }
    }

    private fun readJson(connection: HttpURLConnection, errorStream: Boolean = false): String {
            val mediaType = connection.contentType?.substringBefore(';')?.trim()?.lowercase()
            if (mediaType != "application/json" &&
                mediaType?.let { it.startsWith("application/") && it.endsWith("+json") } != true
            ) {
                throw SafeClientFailure(ApiClientErrorCode.INVALID_CONTENT_TYPE)
            }
            val source = if (errorStream) connection.errorStream
                ?: throw SafeClientFailure(ApiClientErrorCode.HTTP_ERROR) else connection.inputStream
            val bytes = source.use { stream ->
                val output = ByteArrayOutputStream()
                val buffer = ByteArray(8 * 1024)
                while (true) {
                    val count = stream.read(buffer)
                    if (count < 0) break
                    if (output.size() + count > maximumResponseBytes) {
                        throw SafeClientFailure(ApiClientErrorCode.RESPONSE_TOO_LARGE)
                    }
                    output.write(buffer, 0, count)
                }
                output.toByteArray()
            }
            return try {
                StandardCharsets.UTF_8.newDecoder()
                    .onMalformedInput(CodingErrorAction.REPORT)
                    .onUnmappableCharacter(CodingErrorAction.REPORT)
                    .decode(ByteBuffer.wrap(bytes)).toString()
            } catch (_: Exception) {
                throw SafeClientFailure(ApiClientErrorCode.INVALID_JSON)
            }
    }

    private class SafeClientFailure(val code: ApiClientErrorCode) : Exception()
}
