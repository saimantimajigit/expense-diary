package com.expensediary.android.sync

import retrofit2.Response
import retrofit2.http.Body
import retrofit2.http.POST

interface ExpenseDiaryApi {
    @POST("api/v1/transactions/ingest")
    suspend fun ingest(@Body request: IngestRequest): Response<IngestResponse>
}
