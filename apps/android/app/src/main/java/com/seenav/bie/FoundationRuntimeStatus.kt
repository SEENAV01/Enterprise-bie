package com.seenav.bie

import com.seenav.bie.api.ConnectionCheckResult

enum class FoundationStage {
    ANDROID_FOUNDATION,
    API_CONNECTIVITY,
}

data class FoundationRuntimeStatus(
    val backendConnected: Boolean,
    val documentIntelligenceConnected: Boolean,
    val stage: FoundationStage,
) {
    companion object {
        fun initial(): FoundationRuntimeStatus = FoundationRuntimeStatus(
            backendConnected = false,
            documentIntelligenceConnected = false,
            stage = FoundationStage.ANDROID_FOUNDATION,
        )

        fun fromConnectionResult(result: ConnectionCheckResult): FoundationRuntimeStatus =
            if (result.backendConnected && result.documentIntelligenceConnected && result.error == null) {
                FoundationRuntimeStatus(true, true, FoundationStage.API_CONNECTIVITY)
            } else {
                initial()
            }
    }
}
