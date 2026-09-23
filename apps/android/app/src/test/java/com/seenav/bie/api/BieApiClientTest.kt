package com.seenav.bie.api

import com.sun.net.httpserver.HttpExchange
import com.sun.net.httpserver.HttpServer
import java.net.InetSocketAddress
import java.nio.charset.StandardCharsets
import java.util.concurrent.atomic.AtomicInteger
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.jsonObject
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Before
import org.junit.Test

class BieApiClientTest {
    private lateinit var server: HttpServer
    private lateinit var baseUrl: String
    private lateinit var healthBody: String
    private lateinit var capabilitiesBody: String
    private var serverRunning = false
    private val capabilityRequests = AtomicInteger()
    private var health = Reply(200, "")
    private var capabilities = Reply(200, "")

    @Before fun startServer() {
        val fixture = javaClass.classLoader!!.getResourceAsStream("canonical_api_contract.json")!!.use {
            it.readBytes().toString(StandardCharsets.UTF_8)
        }
        val root = Json.parseToJsonElement(fixture).jsonObject
        healthBody = root.getValue("health").toString()
        capabilitiesBody = root.getValue("capabilities").toString()
        health = Reply(200, healthBody)
        capabilities = Reply(200, capabilitiesBody)
        capabilityRequests.set(0)
        server = HttpServer.create(InetSocketAddress("127.0.0.1", 0), 0)
        server.createContext("/healthz") { exchange -> send(exchange, health) }
        server.createContext("/v1/capabilities") { exchange ->
            capabilityRequests.incrementAndGet()
            send(exchange, capabilities)
        }
        server.start()
        serverRunning = true
        baseUrl = "http://127.0.0.1:${server.address.port}"
    }

    @After fun stopServer() {
        if (serverRunning) server.stop(0)
    }

    private fun client(maxBytes: Int = 256 * 1024) = BieApiClient(
        BieApiConfig.from(baseUrl, allowDebugHttp = true),
        maximumResponseBytes = maxBytes,
    )

    private fun send(exchange: HttpExchange, reply: Reply) {
        try {
            reply.contentType?.let { type -> exchange.responseHeaders.set("Content-Type", type) }
            reply.location?.let { location -> exchange.responseHeaders.set("Location", location) }
            val bytes = reply.body.toByteArray(StandardCharsets.UTF_8)
            exchange.sendResponseHeaders(reply.status, bytes.size.toLong())
            exchange.responseBody.use { it.write(bytes) }
        } finally {
            exchange.close()
        }
    }

    private data class Reply(
        val status: Int,
        val body: String,
        val contentType: String? = "application/json; charset=utf-8",
        val location: String? = null,
    )

    private fun assertFailure(expected: ApiClientErrorCode) {
        val result = client().checkConnection()
        assertFalse(result.backendConnected)
        assertFalse(result.documentIntelligenceConnected)
        assertEquals(expected, result.error)
    }

    @Test fun exactHealthAndCapabilitiesConnect() {
        val result = client().checkConnection()
        assertTrue(result.backendConnected)
        assertTrue(result.documentIntelligenceConnected)
        assertEquals(null, result.error)
        assertEquals(1, capabilityRequests.get())
    }

    @Test fun canonicalFixtureMatchesTypedGovernedContract() {
        assertTrue(ApiJson.health(healthBody).matchesContract())
        assertTrue(ApiJson.capabilities(capabilitiesBody).matchesContract())
    }

    @Test fun healthHttpErrorStopsBeforeCapabilities() {
        health = Reply(503, "secret server detail")
        assertFailure(ApiClientErrorCode.HTTP_ERROR)
        assertEquals(0, capabilityRequests.get())
    }

    @Test fun malformedHealthJsonFailsClosed() {
        health = Reply(200, "{")
        assertFailure(ApiClientErrorCode.INVALID_JSON)
    }

    @Test fun wrongHealthServiceFailsClosed() {
        health = Reply(200, healthBody.replace("bie-api", "other-service"))
        assertFailure(ApiClientErrorCode.HEALTH_CONTRACT_MISMATCH)
    }

    @Test fun wrongHealthApiVersionFailsClosed() {
        health = Reply(200, healthBody.replace("v1", "v2"))
        assertFailure(ApiClientErrorCode.HEALTH_CONTRACT_MISMATCH)
    }

    @Test fun capabilityHttpErrorFailsClosed() {
        capabilities = Reply(500, "secret server detail")
        assertFailure(ApiClientErrorCode.HTTP_ERROR)
    }

    @Test fun malformedCapabilitiesJsonFailsClosed() {
        capabilities = Reply(200, "not json")
        assertFailure(ApiClientErrorCode.INVALID_JSON)
    }

    @Test fun persistenceFalseIsRejected() = capabilityMismatch("\"persistence\":true", "\"persistence\":false")
    @Test fun asyncJobsFalseIsRejected() = capabilityMismatch("\"async_jobs\":true", "\"async_jobs\":false")
    @Test fun authenticationTrueIsRejected() = capabilityMismatch("\"authentication\":false", "\"authentication\":true")
    @Test fun productAcceptedTrueIsRejected() = capabilityMismatch("\"product_accepted\":false", "\"product_accepted\":true")
    @Test fun statelessTrueIsRejected() = capabilityMismatch("\"stateless\":false", "\"stateless\":true")
    @Test fun documentInspectionDriftIsRejected() = capabilityMismatch("native_pdf_toc_v1", "other_runtime")
    @Test fun persistenceBackendDriftIsRejected() = capabilityMismatch("local_sqlite_cas_v1", "cloud")
    @Test fun workerModeDriftIsRejected() = capabilityMismatch("local_manual_run_once_v1", "automatic")
    @Test fun capabilityApiVersionDriftIsRejected() = capabilityMismatch("\"api_version\":\"v1\"", "\"api_version\":\"v2\"")

    private fun capabilityMismatch(before: String, after: String) {
        assertTrue(capabilitiesBody.contains(before))
        capabilities = Reply(200, capabilitiesBody.replace(before, after))
        assertFailure(ApiClientErrorCode.CAPABILITY_CONTRACT_MISMATCH)
    }

    @Test fun redirectIsNotFollowed() {
        health = Reply(302, "redirect body", location = "$baseUrl/v1/capabilities")
        assertFailure(ApiClientErrorCode.HTTP_ERROR)
        assertEquals(0, capabilityRequests.get())
    }

    @Test fun oversizedResponseIsRejected() {
        health = Reply(200, "x".repeat(1024))
        val result = client(maxBytes = 128).checkConnection()
        assertEquals(ApiClientErrorCode.RESPONSE_TOO_LARGE, result.error)
    }

    @Test fun nonJsonContentTypeIsRejected() {
        health = Reply(200, healthBody, contentType = "text/plain")
        assertFailure(ApiClientErrorCode.INVALID_CONTENT_TYPE)
    }

    @Test fun rawResponseBodyIsNotInFailure() {
        health = Reply(500, "private-secret-response")
        assertFalse(client().checkConnection().toString().contains("private-secret-response"))
    }

    @Test fun exceptionDetailsAreNotInFailure() {
        server.stop(0)
        serverRunning = false
        val result = client().checkConnection()
        assertEquals(ApiClientErrorCode.NETWORK_UNAVAILABLE, result.error)
        assertFalse(result.toString().contains("ConnectException"))
    }

    @Test fun healthOnlyNeverConnects() {
        capabilities = Reply(503, "unavailable")
        val result = client().checkConnection()
        assertFalse(result.backendConnected)
        assertFalse(result.documentIntelligenceConnected)
        assertEquals(1, capabilityRequests.get())
    }

    @Test fun missingRequiredCapabilityFieldIsInvalidJson() {
        assertTrue(capabilitiesBody.contains(",\"worker_mode\":\"local_manual_run_once_v1\""))
        capabilities = Reply(200, capabilitiesBody.replace(",\"worker_mode\":\"local_manual_run_once_v1\"", ""))
        assertFailure(ApiClientErrorCode.INVALID_JSON)
    }

    @Test fun unknownFutureFieldIsIgnored() {
        health = Reply(200, healthBody.dropLast(1) + ",\"future_field\":123}")
        assertTrue(client().checkConnection().backendConnected)
    }
}
