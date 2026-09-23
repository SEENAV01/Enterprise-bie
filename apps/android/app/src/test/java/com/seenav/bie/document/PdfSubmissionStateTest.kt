package com.seenav.bie.document

import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.ApiJob
import java.io.File
import org.junit.Assert.*
import org.junit.Test

class PdfSubmissionStateTest {
    private val pdf = PreparedPdf("book.pdf", File("unused"), 4, "a".repeat(64), "key")
    @Test fun initialHasNoDocument() { assertNull(PdfSubmissionState().prepared) }
    @Test fun cancellationCanRetainSafeState() { assertEquals(PdfSubmissionStage.NO_DOCUMENT, PdfSubmissionState().stage) }
    @Test fun preparationEntersReady() { assertEquals(PdfSubmissionStage.READY_TO_SUBMIT, PdfSubmissionState().ready(pdf).stage) }
    @Test fun disconnectedCannotSubmit() { assertFalse(PdfSubmissionState().ready(pdf).canSubmit(false, true)) }
    @Test fun partialConnectionCannotSubmit() { assertFalse(PdfSubmissionState().ready(pdf).canSubmit(true, false)) }
    @Test fun connectedAndPreparedCanSubmit() { assertTrue(PdfSubmissionState().ready(pdf).canSubmit(true, true)) }
    @Test fun submittingPreventsDuplicate() { assertFalse(PdfSubmissionState().ready(pdf).submitting().canSubmit(true, true)) }
    @Test fun successRetainsJobIdentity() { val job = ApiJob("job-" + "a".repeat(64), "READY", "b".repeat(64), false); assertEquals(job, PdfSubmissionState().ready(pdf).submitted(job).job) }
    @Test fun failureDoesNotClaimSubmitted() { assertEquals(PdfSubmissionStage.FAILED, PdfSubmissionState().ready(pdf).failed(ApiClientErrorCode.NETWORK_UNAVAILABLE).stage) }
    @Test fun replacementClearsOldJob() { val old = PdfSubmissionState(job = ApiJob("old", "READY", "hash", false)); assertNull(old.ready(pdf).job) }
}
