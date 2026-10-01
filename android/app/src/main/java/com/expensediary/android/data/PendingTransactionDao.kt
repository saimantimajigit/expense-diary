package com.expensediary.android.data

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.OnConflictStrategy
import androidx.room.Query

@Dao
interface PendingTransactionDao {
    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insert(transaction: PendingTransactionEntity)

    @Query("SELECT * FROM pending_transactions WHERE status = 'PENDING' ORDER BY createdAt LIMIT 1")
    suspend fun nextPending(): PendingTransactionEntity?

    @Query("SELECT COUNT(*) FROM pending_transactions WHERE status = 'PENDING'")
    suspend fun pendingCount(): Int

    @Query("SELECT COUNT(*) FROM pending_transactions WHERE status = 'FAILED'")
    suspend fun failedCount(): Int

    @Query("UPDATE pending_transactions SET status = :status, attempts = :attempts, lastError = :error WHERE eventId = :eventId")
    suspend fun setStatus(eventId: String, status: String, attempts: Int, error: String?)

    @Query("UPDATE pending_transactions SET status = 'PENDING', attempts = 0, lastError = NULL WHERE status = 'FAILED'")
    suspend fun retryFailed()
}
