package com.seenav.bie

enum class FoundationStage {
    ANDROID_FOUNDATION,
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
    }
}
