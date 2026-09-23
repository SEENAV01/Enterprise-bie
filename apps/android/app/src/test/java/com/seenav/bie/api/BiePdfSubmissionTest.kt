package com.seenav.bie.api

import com.seenav.bie.document.PreparedPdf
import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.nio.file.Files
import java.security.MessageDigest
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class BiePdfSubmissionTest {
    private lateinit var server: HttpServer
    private lateinit var root: java.io.File
    private lateinit var pdf: PreparedPdf
    private lateinit var base: String
    private val payload = "%PDF-1.7\nfixture".toByteArray()
    private var code = 202
    private var responseType = "application/json"
    private var reply = ""
    private var requestMethod = ""
    private var requestPath = ""
    private var requestBody = byteArrayOf()
    private var requestLength = ""
    private var contentType = ""
    private var accept = ""
    private var idempotency = ""
    private val jobId = "job-" + "a".repeat(64)
    private val hash by lazy { MessageDigest.getInstance("SHA-256").digest(payload).joinToString("") {
        (it.toInt() and 0xff).toString(16).padStart(2, '0')
    } }

    @Before fun setup() {
        root = Files.createTempDirectory("bie-post-test-").toFile()
        val file = java.io.File(root, "upload.pdf"); file.writeBytes(payload)
        pdf = PreparedPdf("book.pdf", file, payload.size.toLong(), hash, "2e9ff561-0e4b-40d7-bd77-109c3df68d8e")
        reply = success()
        server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/") { exchange -> respond(exchange) }
        server.start()
        base = "http://127.0.0.1:${server.address.port}"
    }
    @After fun cleanup() { server.stop(0); root.deleteRecursively() }
    private fun client(max: Int = 256 * 1024) = BieApiClient(BieApiConfig.from(base, true), maximumResponseBytes = max)
    private fun success(id: String = jobId, status: String = "READY", source: String = hash, available: Boolean = false, schema: String = "1.0") =
        """{"api_schema_version":"$schema","job":{"job_id":"$id","status":"$status","source_hash":"$source","result_available":$available}}"""
    private fun respond(exchange: HttpExchange) {
        requestMethod = exchange.requestMethod; requestPath = exchange.requestURI.path
        requestLength = exchange.requestHeaders.getFirst("Content-length") ?: ""
        contentType = exchange.requestHeaders.getFirst("Content-type") ?: ""
        accept = exchange.requestHeaders.getFirst("Accept") ?: ""
        idempotency = exchange.requestHeaders.getFirst("Idempotency-Key") ?: ""
        requestBody = exchange.requestBody.use { it.readBytes() }
        exchange.responseHeaders.set("Content-Type", responseType)
        val bytes = reply.toByteArray()
        exchange.sendResponseHeaders(code, bytes.size.toLong())
        exchange.responseBody.use { it.write(bytes) }
        exchange.close()
    }
    private fun fail(expected: ApiClientErrorCode) { assertEquals(expected, client().submitDocument(pdf).error) }

    @Test fun usesPost() { client().submitDocument(pdf); assertEquals("POST", requestMethod) }
    @Test fun exactEndpoint() { client().submitDocument(pdf); assertEquals("/v1/jobs/document-inspection", requestPath) }
    @Test fun pdfContentType() { client().submitDocument(pdf); assertEquals("application/pdf", contentType) }
    @Test fun acceptsJson() { client().submitDocument(pdf); assertEquals("application/json", accept) }
    @Test fun sendsIdempotencyKey() { client().submitDocument(pdf); assertEquals(pdf.idempotencyKey, idempotency) }
    @Test fun bodyMatchesStagedBytes() { client().submitDocument(pdf); assertArrayEquals(payload, requestBody) }
    @Test fun requestLengthMatches() { client().submitDocument(pdf); assertEquals(payload.size.toString(), requestLength) }
    @Test fun valid202Parses() { assertEquals(jobId, client().submitDocument(pdf).job!!.jobId) }
    @Test fun schemaDriftRejected() { reply = success(schema = "2.0"); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun malformedJobIdRejected() { reply = success(id = "bad"); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun malformedHashRejected() { reply = success(source = "bad"); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun hashMismatchRejected() { reply = success(source = "b".repeat(64)); fail(ApiClientErrorCode.SOURCE_HASH_MISMATCH) }
    @Test fun missingFieldRejected() { reply = success().replace(",\"result_available\":false", ""); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun invalidStatusRejected() { reply = success(status = "UNKNOWN"); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun inconsistentResultAvailabilityRejected() { reply = success(available = true); fail(ApiClientErrorCode.SUBMISSION_CONTRACT_MISMATCH) }
    @Test fun conflictMapped() { code = 409; reply = "private"; fail(ApiClientErrorCode.IDEMPOTENCY_CONFLICT) }
    @Test fun tooLargeMapped() { code = 413; reply = "private"; fail(ApiClientErrorCode.DOCUMENT_TOO_LARGE) }
    @Test fun serverErrorMapped() { code = 500; reply = "private"; fail(ApiClientErrorCode.HTTP_ERROR) }
    @Test fun redirectNotFollowed() { code = 302; fail(ApiClientErrorCode.HTTP_ERROR) }
    @Test fun oversizedJsonRejected() { reply = "x".repeat(1024); assertEquals(ApiClientErrorCode.RESPONSE_TOO_LARGE, client(128).submitDocument(pdf).error) }
    @Test fun nonJsonRejected() { responseType = "text/plain"; fail(ApiClientErrorCode.INVALID_CONTENT_TYPE) }
    @Test fun noRawBodyInSafeError() { code = 500; reply = "private-secret"; assertFalse(client().submitDocument(pdf).toString().contains("private-secret")) }
    @Test fun noExceptionDetailInSafeError() {
        val unavailable = BieApiClient(BieApiConfig.from("http://127.0.0.1:1", true), connectTimeoutMillis = 200)
        assertFalse(unavailable.submitDocument(pdf).toString().contains("ConnectException"))
    }
    @Test fun retryReusesSameKey() { code = 500; client().submitDocument(pdf); val first = idempotency; code = 202; client().submitDocument(pdf); assertEquals(first, idempotency) }
    @Test fun changedSizeFileRejected() { pdf.cacheFile.appendText("extra"); fail(ApiClientErrorCode.DOCUMENT_READ_FAILED) }
    @Test fun oversizedStagedLengthRejected() { val tooLarge = pdf.copy(byteLength = 25L * 1024 * 1024 + 1); assertEquals(ApiClientErrorCode.DOCUMENT_TOO_LARGE, client().submitDocument(tooLarge).error) }
}
