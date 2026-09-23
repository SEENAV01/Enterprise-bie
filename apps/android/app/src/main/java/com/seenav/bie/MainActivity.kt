package com.seenav.bie

import android.os.Bundle
import android.net.Uri
import android.provider.OpenableColumns
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.Button
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.material3.Text
import androidx.compose.material3.lightColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.res.stringResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.seenav.bie.api.ApiClientErrorCode
import com.seenav.bie.api.BieApiClient
import com.seenav.bie.api.BieApiConfig
import com.seenav.bie.document.PdfUploadPreparer
import com.seenav.bie.document.PdfSubmissionStage
import com.seenav.bie.document.PdfSubmissionState
import com.seenav.bie.document.PreparationResult
import com.seenav.bie.document.PreparedPdf
import java.util.concurrent.Executors

class MainActivity : ComponentActivity() {
    private val connectionExecutor = Executors.newSingleThreadExecutor()
    private val apiConfig by lazy {
        BieApiConfig.from(BuildConfig.BIE_API_BASE_URL, allowDebugHttp = BuildConfig.DEBUG)
    }
    private var runtimeStatus by mutableStateOf(FoundationRuntimeStatus.initial())
    private var checking by mutableStateOf(false)
    private var failure by mutableStateOf<ApiClientErrorCode?>(null)
    private var submission by mutableStateOf(PdfSubmissionState())
    private val preparer by lazy { PdfUploadPreparer(cacheDir) }
    private val pdfPicker = registerForActivityResult(ActivityResultContracts.OpenDocument()) { uri: Uri? ->
        if (uri != null) prepareSelection(uri)
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        connectionExecutor.execute { preparer.cleanStale() }
        setContent {
            BieFoundationApp(
                status = runtimeStatus,
                configured = apiConfig.error != ApiClientErrorCode.API_NOT_CONFIGURED,
                checking = checking,
                failure = failure,
                onCheckConnection = ::checkConnection,
                submission = submission,
                onChoosePdf = { pdfPicker.launch(arrayOf("application/pdf")) },
                onSubmitPdf = ::submitPdf,
            )
        }
    }

    private fun prepareSelection(uri: Uri) {
        val previous = submission.prepared
        submission = submission.preparing()
        connectionExecutor.execute {
            preparer.remove(previous)
            val result = try {
                val mime = contentResolver.getType(uri)
                if (mime != null && mime != "application/pdf") {
                    PreparationResult(error = ApiClientErrorCode.INVALID_DOCUMENT_TYPE)
                } else {
                    val name = contentResolver.query(uri, arrayOf(OpenableColumns.DISPLAY_NAME), null, null, null)?.use { cursor ->
                        if (cursor.moveToFirst()) cursor.getString(0) else null
                    }
                    val stream = contentResolver.openInputStream(uri)
                    if (stream == null) PreparationResult(error = ApiClientErrorCode.DOCUMENT_READ_FAILED)
                    else preparer.prepare(stream, name)
                }
            } catch (_: Exception) {
                PreparationResult(error = ApiClientErrorCode.DOCUMENT_READ_FAILED)
            }
            runOnUiThread {
                if (isDestroyed) preparer.remove(result.prepared)
                else submission = if (result.prepared != null) submission.ready(result.prepared)
                else submission.failed(result.error ?: ApiClientErrorCode.DOCUMENT_READ_FAILED)
            }
        }
    }

    private fun submitPdf() {
        if (!submission.canSubmit(runtimeStatus.backendConnected, runtimeStatus.documentIntelligenceConnected)) return
        val prepared = submission.prepared ?: return
        submission = submission.submitting()
        connectionExecutor.execute {
            val result = BieApiClient(apiConfig).submitDocument(prepared)
            if (result.job != null) preparer.remove(prepared)
            runOnUiThread {
                if (isDestroyed) preparer.remove(prepared)
                else submission = if (result.job != null) submission.submitted(result.job)
                else submission.failed(result.error ?: ApiClientErrorCode.INTERNAL_CLIENT_ERROR)
            }
        }
    }

    private fun checkConnection() {
        if (checking) return
        runtimeStatus = FoundationRuntimeStatus.initial()
        apiConfig.error?.let {
            failure = it
            return
        }
        failure = null
        checking = true
        connectionExecutor.execute {
            val result = BieApiClient(apiConfig).checkConnection()
            runOnUiThread {
                if (!isDestroyed) {
                    runtimeStatus = FoundationRuntimeStatus.fromConnectionResult(result)
                    failure = result.error
                    checking = false
                }
            }
        }
    }

    override fun onDestroy() {
        preparer.remove(submission.prepared)
        connectionExecutor.shutdownNow()
        super.onDestroy()
    }
}

@Composable
fun BieFoundationApp(
    status: FoundationRuntimeStatus = FoundationRuntimeStatus.initial(),
    configured: Boolean = false,
    checking: Boolean = false,
    failure: ApiClientErrorCode? = null,
    onCheckConnection: () -> Unit = {},
    submission: PdfSubmissionState = PdfSubmissionState(),
    onChoosePdf: () -> Unit = {},
    onSubmitPdf: () -> Unit = {},
) {
    val colors = lightColorScheme(
        primary = Color(0xFF1F4E5F),
        secondary = Color(0xFF526670),
        background = Color(0xFFF6F8F9),
        surface = Color.White,
    )

    MaterialTheme(colorScheme = colors) {
        Surface(
            modifier = Modifier.fillMaxSize(),
            color = MaterialTheme.colorScheme.background,
        ) {
            Column(
                modifier = Modifier
                    .fillMaxSize()
                    .verticalScroll(rememberScrollState())
                    .padding(horizontal = 24.dp, vertical = 40.dp),
                verticalArrangement = Arrangement.Top,
            ) {
                Text(
                    text = stringResource(R.string.app_name),
                    style = MaterialTheme.typography.headlineMedium,
                    fontWeight = FontWeight.Bold,
                    color = MaterialTheme.colorScheme.primary,
                )
                Spacer(modifier = Modifier.height(8.dp))
                Text(
                    text = stringResource(R.string.foundation_subtitle),
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.secondary,
                )
                Spacer(modifier = Modifier.height(28.dp))
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    shape = RoundedCornerShape(16.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surface,
                    ),
                ) {
                    Column(
                        modifier = Modifier.padding(20.dp),
                        verticalArrangement = Arrangement.spacedBy(18.dp),
                    ) {
                        StatusRow(
                            label = stringResource(R.string.engine_connection_label),
                            connected = status.backendConnected,
                            disconnectedLabel = if (!configured) {
                                stringResource(R.string.not_configured_status)
                            } else {
                                stringResource(R.string.not_connected_status)
                            },
                        )
                        StatusRow(
                            label = stringResource(R.string.document_intelligence_label),
                            connected = status.documentIntelligenceConnected,
                        )
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically,
                        ) {
                            Text(
                                text = stringResource(R.string.build_stage_label),
                                style = MaterialTheme.typography.bodyMedium,
                            )
                            Text(
                                text = when (status.stage) {
                                    FoundationStage.ANDROID_FOUNDATION -> {
                                        stringResource(R.string.foundation_stage_status)
                                    }
                                    FoundationStage.API_CONNECTIVITY -> {
                                        stringResource(R.string.api_connectivity_stage_status)
                                    }
                                },
                                style = MaterialTheme.typography.bodyMedium,
                                fontWeight = FontWeight.SemiBold,
                                color = MaterialTheme.colorScheme.primary,
                            )
                        }
                    }
                }
                Spacer(modifier = Modifier.height(20.dp))
                Button(onClick = onCheckConnection, enabled = !checking) {
                    Text(
                        if (checking) stringResource(R.string.checking_connection_status)
                        else stringResource(R.string.check_connection_action),
                    )
                }
                if (failure != null) {
                    Spacer(modifier = Modifier.height(8.dp))
                    Text(
                        text = stringResource(R.string.connection_failure_code, failure.name),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error,
                    )
                }
                Text(
                    text = stringResource(R.string.connection_notice),
                    style = MaterialTheme.typography.bodySmall,
                    color = MaterialTheme.colorScheme.secondary,
                )
                Spacer(modifier = Modifier.height(24.dp))
                Button(onClick = onChoosePdf, enabled = submission.stage !in setOf(
                    PdfSubmissionStage.PREPARING, PdfSubmissionStage.SUBMITTING,
                )) { Text(stringResource(R.string.choose_pdf_action)) }
                submission.prepared?.let { document ->
                    Text(document.displayName, style = MaterialTheme.typography.bodyMedium)
                    Text(stringResource(R.string.pdf_size_bytes, document.byteLength),
                        style = MaterialTheme.typography.bodySmall)
                }
                Text(submission.stage.name, style = MaterialTheme.typography.bodySmall)
                Button(
                    onClick = onSubmitPdf,
                    enabled = submission.canSubmit(status.backendConnected, status.documentIntelligenceConnected),
                ) { Text(stringResource(R.string.submit_pdf_action)) }
                submission.job?.let { job ->
                    Text(stringResource(R.string.pdf_job_submitted, job.jobId.take(12), job.status),
                        style = MaterialTheme.typography.bodyMedium)
                }
                submission.error?.let { code ->
                    Text(stringResource(R.string.pdf_submission_error, code.name),
                        style = MaterialTheme.typography.bodySmall,
                        color = MaterialTheme.colorScheme.error)
                }
            }
        }
    }
}

@Composable
private fun StatusRow(
    label: String,
    connected: Boolean,
    disconnectedLabel: String? = null,
) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Text(
            text = label,
            style = MaterialTheme.typography.bodyMedium,
        )
        Text(
            text = if (connected) {
                stringResource(R.string.connected_status)
            } else {
                disconnectedLabel ?: stringResource(R.string.not_connected_status)
            },
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
            color = if (connected) Color(0xFF1B6B45) else Color(0xFF9B3A2E),
        )
    }
}
