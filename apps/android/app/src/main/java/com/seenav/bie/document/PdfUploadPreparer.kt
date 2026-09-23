package com.seenav.bie.document

import com.seenav.bie.api.ApiClientErrorCode
import java.io.File
import java.io.InputStream
import java.security.MessageDigest
import java.util.UUID

const val MAX_PDF_BYTES: Long = 25L * 1024 * 1024

data class PreparedPdf(
    val displayName: String,
    val cacheFile: File,
    val byteLength: Long,
    val sourceSha256: String,
    val idempotencyKey: String,
)

data class PreparationResult(val prepared: PreparedPdf? = null, val error: ApiClientErrorCode? = null)

class PdfUploadPreparer(private val cacheRoot: File) {
    private val uploadDir get() = File(cacheRoot, "bie-pdf-upload")

    fun prepare(input: InputStream, displayName: String?): PreparationResult {
        if (!uploadDir.isDirectory && !uploadDir.mkdirs()) {
            runCatching { input.close() }
            return PreparationResult(error = ApiClientErrorCode.DOCUMENT_READ_FAILED)
        }
        var staged: File? = null
        return try {
            val target = File.createTempFile("upload-", ".pdf", uploadDir)
            staged = target
            val digest = MessageDigest.getInstance("SHA-256")
            var length = 0L
            input.use { source ->
                target.outputStream().use { sink ->
                    val buffer = ByteArray(8 * 1024)
                    while (true) {
                        val count = source.read(buffer)
                        if (count < 0) break
                        length += count
                        if (length > MAX_PDF_BYTES) throw OversizedDocument()
                        sink.write(buffer, 0, count)
                        digest.update(buffer, 0, count)
                    }
                }
            }
            if (length == 0L) {
                target.delete()
                PreparationResult(error = ApiClientErrorCode.EMPTY_DOCUMENT)
            } else PreparationResult(prepared = PreparedPdf(
                displayName = displayName?.takeIf { it.isNotBlank() } ?: "Selected PDF",
                cacheFile = target,
                byteLength = length,
                sourceSha256 = digest.digest().joinToString("") {
                    (it.toInt() and 0xff).toString(16).padStart(2, '0')
                },
                idempotencyKey = UUID.randomUUID().toString(),
            ))
        } catch (_: OversizedDocument) {
            staged?.delete()
            PreparationResult(error = ApiClientErrorCode.DOCUMENT_TOO_LARGE)
        } catch (_: Exception) {
            staged?.delete()
            PreparationResult(error = ApiClientErrorCode.DOCUMENT_READ_FAILED)
        }
    }

    fun remove(prepared: PreparedPdf?) { prepared?.cacheFile?.delete() }

    fun cleanStale() {
        uploadDir.listFiles()?.filter { it.isFile && it.name.startsWith("upload-") }?.forEach { it.delete() }
    }

    private class OversizedDocument : Exception()
}
