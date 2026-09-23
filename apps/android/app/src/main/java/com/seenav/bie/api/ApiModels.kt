package com.seenav.bie.api

import kotlinx.serialization.json.Json
import kotlinx.serialization.json.JsonObject
import kotlinx.serialization.json.JsonPrimitive
import kotlinx.serialization.json.booleanOrNull
import kotlinx.serialization.json.jsonObject
import kotlinx.serialization.json.contentOrNull

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
}
