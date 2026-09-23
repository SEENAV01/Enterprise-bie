package com.seenav.bie

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ConnectionCheckResult
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class FoundationRuntimeStatusTest {
    @Test
    fun initialStateIsFailClosed() {
        val status = FoundationRuntimeStatus.initial()

        assertFalse(status.backendConnected)
        assertFalse(status.documentIntelligenceConnected)
        assertEquals(FoundationStage.ANDROID_FOUNDATION, status.stage)
    }

    @Test fun completeSuccessConnectsBothBoundaries() {
        val status = FoundationRuntimeStatus.fromConnectionResult(ConnectionCheckResult.connected())
        assertTrue(status.backendConnected)
        assertTrue(status.documentIntelligenceConnected)
        assertEquals(FoundationStage.API_CONNECTIVITY, status.stage)
    }

    @Test fun failureKeepsBothBoundariesDisconnected() {
        val status = FoundationRuntimeStatus.fromConnectionResult(
            ConnectionCheckResult.failed(ApiClientErrorCode.CAPABILITY_CONTRACT_MISMATCH),
        )
        assertFalse(status.backendConnected)
        assertFalse(status.documentIntelligenceConnected)
    }

    @Test fun healthOnlySuccessDoesNotConnect() {
        val status = FoundationRuntimeStatus.fromConnectionResult(
            ConnectionCheckResult(backendConnected = true, documentIntelligenceConnected = false),
        )
        assertFalse(status.backendConnected)
        assertFalse(status.documentIntelligenceConnected)
    }

    @Test fun errorOverridesAccidentalConnectionFlags() {
        val status = FoundationRuntimeStatus.fromConnectionResult(
            ConnectionCheckResult(true, true, ApiClientErrorCode.INTERNAL_CLIENT_ERROR),
        )
        assertFalse(status.backendConnected)
        assertFalse(status.documentIntelligenceConnected)
    }
}
