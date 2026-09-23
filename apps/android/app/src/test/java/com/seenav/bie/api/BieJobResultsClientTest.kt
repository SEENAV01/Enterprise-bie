package com.seenav.bie.api

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class BieJobResultsClientTest {
    private lateinit var server: HttpServer
    private lateinit var base: String
    private val id = "job-" + "a".repeat(64)
    private val hash = "b".repeat(64)
    private var code = 200
    private var reply = ""
    private var responseType = "application/json"
    private var location: String? = null
    private var path = ""
    private var method = ""
    private var accept = ""
    private var resultRequests = 0

    @Before fun setup() {
        code = 200; reply = statusBody(); responseType = "application/json"
        location = null; resultRequests = 0
        server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/") { exchange -> respond(exchange) }
        server.start()
        base = "http://127.0.0.1:${server.address.port}"
    }

    @After fun cleanup() { server.stop(0) }

    private fun client(max: Int = 256 * 1024) = BieApiClient(BieApiConfig.from(base, true), maximumResponseBytes = max)
    private fun status() = client().getJobStatus(id, hash)
    private fun result() = client().getJobResult(id, hash)
    private fun statusError(expected: ApiClientErrorCode) = assertEquals(expected, status().error)
    private fun resultError(expected: ApiClientErrorCode) = assertEquals(expected, result().error)

    private fun statusBody(
        jobId: String = id, source: String = hash, stage: String = "READY",
        queue: String = "READY", available: Boolean = false, schema: String = "1.0",
    ) = """{"api_schema_version":"$schema","job":{"job_id":"$jobId","status":"$stage","source_hash":"$source","result_available":$available,"queue_state":"$queue"}}"""

    private fun resultBody(jobId: String = id, source: String = hash, schema: String = "1.0") =
        """{"api_schema_version":"$schema","job_id":"$jobId","result":{"source_hash":"$source","byte_length":123,"page_count":2,"total_blocks":4,"hierarchy_policy":"numbered_heading_hierarchy_v1","toc_reconciliation_policy":"native_outline_exact_title_v1","heading_candidate_count":1,"materialized_chapter_count":1,"materialized_section_count":0,"materialized_subsection_count":0,"native_outline_entry_count":0,"outline_resolvable_page_count":0,"reconciliation_match_count":0,"unmatched_outline_count":0,"ambiguous_detected_title_count":0,"exact_page_match_count":0,"outline_status":"no_native_outline","future_field":"ignored"}}"""

    private fun respond(exchange: HttpExchange) {
        method = exchange.requestMethod
        path = exchange.requestURI.path
        accept = exchange.requestHeaders.getFirst("Accept") ?: ""
        if (path.endsWith("/result")) resultRequests++
        exchange.responseHeaders.set("Content-Type", responseType)
        location?.let { exchange.responseHeaders.set("Location", it) }
        val bytes = reply.toByteArray()
        exchange.sendResponseHeaders(code, bytes.size.toLong())
        exchange.responseBody.use { it.write(bytes) }
        exchange.close()
    }

    @Test fun statusPathExact() { status(); assertEquals("/v1/jobs/$id", path) }
    @Test fun statusUsesGet() { status(); assertEquals("GET", method) }
    @Test fun statusAcceptsJson() { status(); assertEquals("application/json", accept) }
    @Test fun readyParses() { assertEquals("READY", status().status?.status) }
    @Test fun runningParses() { reply = statusBody(stage = "RUNNING", queue = "DELIVERED"); assertEquals("RUNNING", status().status?.status) }
    @Test fun succeededParses() { reply = statusBody(stage = "SUCCEEDED", queue = "ACKED", available = true); assertEquals("SUCCEEDED", status().status?.status) }
    @Test fun failedParses() { reply = statusBody(stage = "FAILED", queue = "DEAD_LETTER"); assertEquals("FAILED", status().status?.status) }
    @Test fun statusSchemaMismatchRejected() { reply = statusBody(schema = "2.0"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun missingRequiredStatusFieldRejected() { reply = statusBody().replace(",\"queue_state\":\"READY\"", ""); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun malformedExpectedJobIdRejectedBeforeNetwork() { assertEquals(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH, client().getJobStatus("bad", hash).error) }
    @Test fun malformedStatusJobIdRejected() { reply = statusBody(jobId = "bad"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun statusJobIdMismatchRejected() { reply = statusBody(jobId = "job-" + "c".repeat(64)); statusError(ApiClientErrorCode.JOB_ID_MISMATCH) }
    @Test fun malformedStatusHashRejected() { reply = statusBody(source = "BAD"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun statusHashMismatchRejected() { reply = statusBody(source = "c".repeat(64)); statusError(ApiClientErrorCode.SOURCE_HASH_MISMATCH) }
    @Test fun unknownStatusRejected() { reply = statusBody(stage = "PENDING"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun unknownQueueRejected() { reply = statusBody(queue = "UNKNOWN"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun readyReadyAllowed() { assertNotNull(status().status) }
    @Test fun readyDeliveredAllowed() { reply = statusBody(queue = "DELIVERED"); assertNotNull(status().status) }
    @Test fun runningDeliveredAllowed() { reply = statusBody(stage = "RUNNING", queue = "DELIVERED"); assertNotNull(status().status) }
    @Test fun succeededDeliveredAllowed() { reply = statusBody(stage = "SUCCEEDED", queue = "DELIVERED", available = true); assertNotNull(status().status) }
    @Test fun succeededAckedAllowed() { reply = statusBody(stage = "SUCCEEDED", queue = "ACKED", available = true); assertNotNull(status().status) }
    @Test fun failedDeliveredAllowed() { reply = statusBody(stage = "FAILED", queue = "DELIVERED"); assertNotNull(status().status) }
    @Test fun failedDeadLetterAllowed() { reply = statusBody(stage = "FAILED", queue = "DEAD_LETTER"); assertNotNull(status().status) }
    @Test fun impossibleStatusQueueRejected() { reply = statusBody(stage = "RUNNING", queue = "ACKED"); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun inconsistentAvailableRejected() { reply = statusBody(available = true); statusError(ApiClientErrorCode.JOB_STATUS_CONTRACT_MISMATCH) }
    @Test fun status404Mapped() { code = 404; statusError(ApiClientErrorCode.JOB_NOT_FOUND) }
    @Test fun status500Mapped() { code = 500; statusError(ApiClientErrorCode.HTTP_ERROR) }
    @Test fun statusRedirectNotFollowed() { code = 302; location = "$base/healthz"; statusError(ApiClientErrorCode.HTTP_ERROR) }
    @Test fun statusOversizeRejected() { reply = "x".repeat(1024); assertEquals(ApiClientErrorCode.RESPONSE_TOO_LARGE, client(128).getJobStatus(id, hash).error) }
    @Test fun statusNonJsonRejected() { responseType = "text/plain"; statusError(ApiClientErrorCode.INVALID_CONTENT_TYPE) }
    @Test fun rawStatusErrorAbsent() { code = 500; reply = "private-secret"; assertFalse(status().toString().contains("private-secret")) }

    @Test fun resultPathExact() { reply = resultBody(); result(); assertEquals("/v1/jobs/$id/result", path); assertEquals("GET", method) }
    @Test fun validResultParses() { reply = resultBody(); assertEquals(2, result().result?.summary?.pageCount) }
    @Test fun resultSchemaMismatchRejected() { reply = resultBody(schema = "2.0"); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun malformedExpectedResultHashRejectedBeforeNetwork() { assertEquals(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH, client().getJobResult(id, "BAD").error) }
    @Test fun resultJobMismatchRejected() { reply = resultBody(jobId = "job-" + "c".repeat(64)); resultError(ApiClientErrorCode.JOB_ID_MISMATCH) }
    @Test fun resultHashMismatchRejected() { reply = resultBody(source = "c".repeat(64)); resultError(ApiClientErrorCode.SOURCE_HASH_MISMATCH) }
    @Test fun zeroByteLengthRejected() { reply = resultBody().replace("\"byte_length\":123", "\"byte_length\":0"); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun zeroPagesRejected() { reply = resultBody().replace("\"page_count\":2", "\"page_count\":0"); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun negativeCountRejected() { reply = resultBody().replace("\"total_blocks\":4", "\"total_blocks\":-1"); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun missingRequiredCountRejected() { reply = resultBody().replace("\"total_blocks\":4,", ""); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun unknownOutlineStatusRejected() { reply = resultBody().replace("no_native_outline", "unknown"); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun emptyHierarchyPolicyRejected() { reply = resultBody().replace("numbered_heading_hierarchy_v1", ""); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun emptyTocPolicyRejected() { reply = resultBody().replace("native_outline_exact_title_v1", ""); resultError(ApiClientErrorCode.JOB_RESULT_CONTRACT_MISMATCH) }
    @Test fun result404Mapped() { code = 404; resultError(ApiClientErrorCode.JOB_NOT_FOUND) }
    @Test fun resultNotReadyMapped() { code = 409; reply = """{"error":{"code":"result_not_ready"}}"""; resultError(ApiClientErrorCode.RESULT_NOT_READY) }
    @Test fun jobFailedMapped() { code = 409; reply = """{"error":{"code":"job_failed"}}"""; resultError(ApiClientErrorCode.JOB_FAILED) }
    @Test fun unrelated409Mapped() { code = 409; reply = """{"error":{"code":"private_error"}}"""; resultError(ApiClientErrorCode.HTTP_ERROR) }
    @Test fun resultOversizeRejected() { reply = resultBody() + "x".repeat(1024); assertEquals(ApiClientErrorCode.RESPONSE_TOO_LARGE, client(128).getJobResult(id, hash).error) }
    @Test fun rawResultErrorAbsent() { code = 409; reply = "private-secret"; assertFalse(result().toString().contains("private-secret")) }
}
