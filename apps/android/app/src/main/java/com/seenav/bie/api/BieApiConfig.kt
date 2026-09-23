package com.seenav.bie.api

import java.net.URI

data class BieApiConfig private constructor(
    val baseUrl: String?,
    val error: ApiClientErrorCode?,
) {
    companion object {
        fun from(raw: String, allowDebugHttp: Boolean): BieApiConfig {
            if (raw.isBlank()) return BieApiConfig(null, ApiClientErrorCode.API_NOT_CONFIGURED)
            if (raw != raw.trim()) return BieApiConfig(null, ApiClientErrorCode.INVALID_API_BASE_URL)
            return try {
                val uri = URI(raw)
                val scheme = uri.scheme?.lowercase()
                if (
                    (scheme != "https" && scheme != "http") ||
                    (scheme == "http" && !allowDebugHttp) ||
                    uri.host.isNullOrBlank() ||
                    uri.rawUserInfo != null ||
                    uri.rawQuery != null ||
                    uri.rawFragment != null ||
                    uri.rawPath.split('/').any { it == "." || it == ".." } ||
                    uri.port == 0 || uri.port > 65535
                ) {
                    BieApiConfig(null, ApiClientErrorCode.INVALID_API_BASE_URL)
                } else {
                    BieApiConfig(raw.trimEnd('/'), null)
                }
            } catch (_: Exception) {
                BieApiConfig(null, ApiClientErrorCode.INVALID_API_BASE_URL)
            }
        }
    }
}
