package com.expensediary.android.sync

import com.google.gson.annotations.SerializedName
import java.math.BigDecimal

data class IngestRequest(
    val amount: BigDecimal,
    val currency: String,
    @SerializedName("transaction_type") val transactionType: String,
    val merchant: String?,
    val description: String?,
    @SerializedName("payment_app") val paymentApp: String,
    @SerializedName("transaction_reference") val transactionReference: String?,
    @SerializedName("transaction_time") val transactionTime: String,
    val source: String,
    @SerializedName("raw_notification") val rawNotification: String,
    @SerializedName("raw_payload") val rawPayload: Map<String, Any?>,
)

data class IngestResponse(
    val transaction: Map<String, Any?>,
    val duplicate: Boolean,
)
