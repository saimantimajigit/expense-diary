package com.expensediary.android.notification

import android.content.Context
import com.google.gson.GsonBuilder
import com.google.gson.reflect.TypeToken

/** Small, bounded debug history stored on-device in private app preferences. */
class CapturedNotificationStore(context: Context) {
    private val preferences = context.applicationContext.getSharedPreferences(PREFERENCES, Context.MODE_PRIVATE)
    private val gson = GsonBuilder().serializeNulls().create()

    fun latest(): List<PaymentNotificationSnapshot> = synchronized(lock) {
        val json = preferences.getString(KEY_NOTIFICATIONS, null) ?: return@synchronized emptyList()
        runCatching {
            gson.fromJson<List<PaymentNotificationSnapshot>>(json, notificationListType)
        }.getOrNull().orEmpty()
    }

    /** Returns false when this exact Android callback has already been captured. */
    fun add(notification: PaymentNotificationSnapshot): Boolean = synchronized(lock) {
        val current = latest()
        val identity = notification.duplicateKey()
        if (current.any { it.duplicateKey() == identity }) return@synchronized false

        val updated = (listOf(notification) + current).take(MAX_NOTIFICATIONS)
        preferences.edit().putString(KEY_NOTIFICATIONS, gson.toJson(updated, notificationListType)).apply()
        true
    }

    companion object {
        const val ACTION_NOTIFICATIONS_CHANGED = "com.expensediary.android.NOTIFICATIONS_CHANGED"

        private const val PREFERENCES = "captured_google_pay_notifications"
        private const val KEY_NOTIFICATIONS = "latest"
        private const val MAX_NOTIFICATIONS = 50
        private val lock = Any()
        private val notificationListType = object : TypeToken<List<PaymentNotificationSnapshot>>() {}.type
    }
}
