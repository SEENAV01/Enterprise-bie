package com.seenav.bie.api

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class BieApiConfigTest {
    @Test fun blankIsUnconfigured() {
        val config = BieApiConfig.from("  ", true)
        assertNull(config.baseUrl)
        assertEquals(ApiClientErrorCode.API_NOT_CONFIGURED, config.error)
    }

    @Test fun httpsIsAccepted() = assertEquals("https://example.org", BieApiConfig.from("https://example.org", false).baseUrl)
    @Test fun debugHttpIsAccepted() = assertEquals("http://127.0.0.1:8765", BieApiConfig.from("http://127.0.0.1:8765", true).baseUrl)
    @Test fun releaseHttpIsRejected() = assertInvalid("http://127.0.0.1:8765", false)
    @Test fun missingHostIsRejected() = assertInvalid("https:///path", true)
    @Test fun userInfoIsRejected() = assertInvalid("https://name:password@example.org", true)
    @Test fun queryIsRejected() = assertInvalid("https://example.org?x=1", true)
    @Test fun fragmentIsRejected() = assertInvalid("https://example.org/#section", true)
    @Test fun trailingSlashIsNormalized() = assertEquals("https://example.org/prefix", BieApiConfig.from("https://example.org/prefix/", false).baseUrl)
    @Test fun malformedUrlIsRejected() = assertInvalid("https://bad host", true)
    @Test fun unsupportedSchemeIsRejected() = assertInvalid("file:///tmp/api", true)
    @Test fun pathTraversalIsRejected() = assertInvalid("https://example.org/a/../b", true)

    private fun assertInvalid(raw: String, debug: Boolean) {
        val config = BieApiConfig.from(raw, debug)
        assertNull(config.baseUrl)
        assertEquals(ApiClientErrorCode.INVALID_API_BASE_URL, config.error)
    }
}
