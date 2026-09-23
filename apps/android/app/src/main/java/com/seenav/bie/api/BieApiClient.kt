package com.seenav.bie.api

import java.io.ByteArrayOutputStream
import java.io.IOException
import java.net.HttpURLConnection
import java.net.URL
import java.nio.ByteBuffer
import java.nio.charset.CodingErrorAction
import java.nio.charset.StandardCharsets

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
) {
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
            val mediaType = connection.contentType?.substringBefore(';')?.trim()?.lowercase()
            if (mediaType != null && mediaType != "application/json" &&
                !(mediaType.startsWith("application/") && mediaType.endsWith("+json"))
            ) {
                throw SafeClientFailure(ApiClientErrorCode.INVALID_CONTENT_TYPE)
            }
            val bytes = connection.inputStream.use { stream ->
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
        } finally {
            connection.disconnect()
        }
    }

    private class SafeClientFailure(val code: ApiClientErrorCode) : Exception()
}
