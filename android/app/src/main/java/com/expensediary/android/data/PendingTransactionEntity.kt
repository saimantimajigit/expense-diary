package com.expensediary.android.data

import androidx.room.Entity
import androidx.room.PrimaryKey

object PendingStatus {
    const val PENDING = "PENDING"
    const val SYNCED = "SYNCED"
    const val FAILED = "FAILED"
}

@Entity(tableName = "pending_transactions")
data class PendingTransactionEntity(
    @PrimaryKey val eventId: String,
    val payloadJson: String,
    val status: String,
    val attempts: Int,
    val createdAt: Long,
    val lastError: String? = null,
)
