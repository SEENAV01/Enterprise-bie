package com.seenav.bie.document

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ApiJob

enum class PdfSubmissionStage { NO_DOCUMENT, PREPARING, READY_TO_SUBMIT, SUBMITTING, SUBMITTED, FAILED }

data class PdfSubmissionState(
    val stage: PdfSubmissionStage = PdfSubmissionStage.NO_DOCUMENT,
    val prepared: PreparedPdf? = null,
    val job: ApiJob? = null,
    val error: ApiClientErrorCode? = null,
) {
    fun canSubmit(backendConnected: Boolean, documentIntelligenceConnected: Boolean): Boolean =
        backendConnected && documentIntelligenceConnected && prepared != null &&
            stage in setOf(PdfSubmissionStage.READY_TO_SUBMIT, PdfSubmissionStage.FAILED)

    fun preparing() = PdfSubmissionState(stage = PdfSubmissionStage.PREPARING)
    fun ready(document: PreparedPdf) = PdfSubmissionState(PdfSubmissionStage.READY_TO_SUBMIT, document)
    fun submitting() = copy(stage = PdfSubmissionStage.SUBMITTING, error = null)
    fun submitted(value: ApiJob) = copy(stage = PdfSubmissionStage.SUBMITTED, prepared = null, job = value, error = null)
    fun failed(code: ApiClientErrorCode) = copy(stage = PdfSubmissionStage.FAILED, job = null, error = code)
}
