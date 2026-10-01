package com.expensediary.android.notification

import android.content.Intent
import android.service.notification.NotificationListenerService
import android.service.notification.StatusBarNotification
import android.util.Log
import com.expensediary.android.BuildConfig
import com.google.gson.Gson
import com.google.gson.GsonBuilder

class PaymentNotificationListenerService : NotificationListenerService() {
    private val parser: PaymentNotificationParser = GooglePayNotificationParser()
    private val gson: Gson = GsonBuilder().serializeNulls().create()

    override fun onListenerConnected() {
        super.onListenerConnected()
        Log.i(LOG_TAG, "Notification listener connected")
    }

    override fun onNotificationPosted(statusBarNotification: StatusBarNotification) {
        if (statusBarNotification.packageName != GooglePayNotificationParser.GOOGLE_PAY_PACKAGE) return

        val extras = statusBarNotification.notification.extras
        val rawNotification = PaymentNotificationSnapshot(
            packageName = statusBarNotification.packageName,
            title = extras.getCharSequence("android.title")?.toString(),
            text = extras.getCharSequence("android.text")?.toString(),
            bigText = extras.getCharSequence("android.bigText")?.toString(),
            subText = extras.getCharSequence("android.subText")?.toString(),
            postTime = statusBarNotification.postTime,
            notificationKey = statusBarNotification.key,
        )
        val captured = parser.parse(rawNotification) ?: return
        val added = CapturedNotificationStore(this).add(captured)

        if (BuildConfig.DEBUG) {
            Log.d(LOG_TAG, "Google Pay notification ${if (added) "captured" else "duplicate callback ignored"}: ${gson.toJson(captured)}")
        }
        if (added) {
            sendBroadcast(Intent(CapturedNotificationStore.ACTION_NOTIFICATIONS_CHANGED).setPackage(packageName))
        }
    }

    override fun onListenerDisconnected() {
        Log.w(LOG_TAG, "Notification listener disconnected; Android may reconnect it")
        super.onListenerDisconnected()
    }

    companion object {
        private const val LOG_TAG = "ExpenseDiaryNotify"
    }
}
