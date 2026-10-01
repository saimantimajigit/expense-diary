package com.expensediary.android.sync

import android.content.Context
import androidx.work.CoroutineWorker
import androidx.work.WorkerParameters
import com.expensediary.android.data.AppDatabase
import com.expensediary.android.data.PendingStatus
import com.google.gson.Gson
import java.io.IOException
import kotlinx.coroutines.CancellationException

class PendingSyncWorker(context: Context, parameters: WorkerParameters) : CoroutineWorker(context, parameters) {
    override suspend fun doWork(): Result {
        val dao = AppDatabase.get(applicationContext).pendingTransactions()
        val pending = dao.nextPending() ?: return Result.success()
        val request = runCatching { Gson().fromJson(pending.payloadJson, IngestRequest::class.java) }
            .getOrNull() ?: run {
            dao.setStatus(pending.eventId, PendingStatus.FAILED, pending.attempts + 1, "Invalid local event")
            return Result.success()
        }

        return try {
            val response = ApiClient.service.ingest(request)
            if (response.isSuccessful) {
                dao.setStatus(pending.eventId, PendingStatus.SYNCED, pending.attempts + 1, null)
                Result.success()
            } else if (response.code() in 400..499) {
                dao.setStatus(
                    pending.eventId,
                    PendingStatus.FAILED,
                    pending.attempts + 1,
                    "Backend rejected event (${response.code()})",
                )
                Result.success()
            } else {
                retryOrFail(dao, pending.eventId, pending.attempts, "Backend unavailable (${response.code()})")
            }
        } catch (error: CancellationException) {
            throw error
        } catch (error: IOException) {
            retryOrFail(dao, pending.eventId, pending.attempts, error.javaClass.simpleName)
        } catch (error: Exception) {
            retryOrFail(dao, pending.eventId, pending.attempts, error.javaClass.simpleName)
        }
    }

    private suspend fun retryOrFail(dao: com.expensediary.android.data.PendingTransactionDao, eventId: String, attempts: Int, error: String): Result {
        val nextAttempt = attempts + 1
        if (nextAttempt >= MAX_ATTEMPTS) {
            dao.setStatus(eventId, PendingStatus.FAILED, nextAttempt, error)
            return Result.success()
        }
        dao.setStatus(eventId, PendingStatus.PENDING, nextAttempt, error)
        return Result.retry()
    }

    companion object {
        const val UNIQUE_WORK_NAME = "expense-diary-pending-sync"
        private const val MAX_ATTEMPTS = 8
    }
}
