package com.seenav.bie.document

import com.seenav.bie.api.ApiClientErrorCode
import java.io.ByteArrayInputStream
import java.io.IOException
import java.io.InputStream
import java.nio.file.Files
import java.security.MessageDigest
import org.junit.After
import org.junit.Assert.*
import org.junit.Before
import org.junit.Test

class PdfUploadPreparerTest {
    private lateinit var root: java.io.File
    private lateinit var preparer: PdfUploadPreparer
    @Before fun setup() { root = Files.createTempDirectory("bie-stager-test-").toFile(); preparer = PdfUploadPreparer(root) }
    @After fun cleanup() { root.deleteRecursively() }
    private val bytes = "%PDF-1.7\nexample".toByteArray()
    private fun stage() = preparer.prepare(ByteArrayInputStream(bytes), "private-book.pdf")
    private fun sized(count: Long) = object : InputStream() {
        var remaining = count
        override fun read(): Int = if (remaining-- > 0) 65 else -1
        override fun read(target: ByteArray, offset: Int, length: Int): Int {
            if (remaining <= 0) return -1
            val size = minOf(length.toLong(), remaining).toInt()
            java.util.Arrays.fill(target, offset, offset + size, 65.toByte())
            remaining -= size
            return size
        }
    }
    @Test fun stagesNormalStream() { assertTrue(stage().prepared!!.cacheFile.isFile) }
    @Test fun computesSha() {
        val expected = MessageDigest.getInstance("SHA-256").digest(bytes).joinToString("") {
            (it.toInt() and 0xff).toString(16).padStart(2, '0')
        }
        assertEquals(expected, stage().prepared!!.sourceSha256)
    }
    @Test fun countsBytes() { assertEquals(bytes.size.toLong(), stage().prepared!!.byteLength) }
    @Test fun rejectsEmpty() { assertEquals(ApiClientErrorCode.EMPTY_DOCUMENT, preparer.prepare(ByteArrayInputStream(byteArrayOf()), null).error) }
    @Test fun acceptsExactLimit() { assertEquals(MAX_PDF_BYTES, preparer.prepare(sized(MAX_PDF_BYTES), null).prepared!!.byteLength) }
    @Test fun rejectsOverLimit() { assertEquals(ApiClientErrorCode.DOCUMENT_TOO_LARGE, preparer.prepare(sized(MAX_PDF_BYTES + 1), null).error) }
    @Test fun deletesOversizePartialFile() { preparer.prepare(sized(MAX_PDF_BYTES + 1), null); assertTrue(java.io.File(root, "bie-pdf-upload").listFiles().isNullOrEmpty()) }
    @Test fun readFailureDeletesPartialFile() {
        val broken = object : InputStream() { var n = 0; override fun read(): Int = if (n++ == 0) 65 else throw IOException("private path") }
        assertEquals(ApiClientErrorCode.DOCUMENT_READ_FAILED, preparer.prepare(broken, null).error)
        assertTrue(java.io.File(root, "bie-pdf-upload").listFiles().isNullOrEmpty())
    }
    @Test fun filenameDoesNotContainOriginal() { assertFalse(stage().prepared!!.cacheFile.name.contains("private-book")) }
    @Test fun replacementCleanupRemovesPrevious() { val first = stage().prepared!!; preparer.remove(first); assertFalse(first.cacheFile.exists()); assertTrue(stage().prepared!!.cacheFile.exists()) }
    @Test fun safeFailureHasNoPath() { assertFalse(preparer.prepare(ByteArrayInputStream(byteArrayOf()), null).toString().contains(root.path)) }
    @Test fun preparedKeyIsStable() { val prepared = stage().prepared!!; assertEquals(prepared.idempotencyKey, prepared.idempotencyKey) }
    @Test fun newPreparationGetsNewKey() { assertNotEquals(stage().prepared!!.idempotencyKey, stage().prepared!!.idempotencyKey) }
    @Test fun staleFilesAreRemoved() { stage(); preparer.cleanStale(); assertTrue(java.io.File(root, "bie-pdf-upload").listFiles().isNullOrEmpty()) }
}
