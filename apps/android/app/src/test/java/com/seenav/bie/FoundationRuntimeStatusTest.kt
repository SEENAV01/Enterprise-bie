package com.seenav.bie

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Test

class FoundationRuntimeStatusTest {
    @Test
    fun initialStateIsFailClosed() {
        val status = FoundationRuntimeStatus.initial()

        assertFalse(status.backendConnected)
        assertFalse(status.documentIntelligenceConnected)
        assertEquals(FoundationStage.ANDROID_FOUNDATION, status.stage)
    }
}
