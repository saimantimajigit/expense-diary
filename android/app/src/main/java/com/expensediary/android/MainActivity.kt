package com.expensediary.android

import android.app.Activity
import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.content.IntentFilter
import android.os.Bundle
import android.provider.Settings
import android.text.format.DateFormat
import android.view.ViewGroup
import android.widget.Button
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import androidx.core.app.NotificationManagerCompat
import androidx.core.content.ContextCompat
import com.expensediary.android.notification.CapturedNotificationStore
import com.expensediary.android.notification.PaymentNotificationSnapshot
import java.util.Date

class MainActivity : Activity() {
    private lateinit var accessStatus: TextView
    private lateinit var notificationsList: TextView
    private var receiverRegistered = false

    private val notificationsChangedReceiver = object : BroadcastReceiver() {
        override fun onReceive(context: Context, intent: Intent) {
            refreshScreen()
        }
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        accessStatus = TextView(this).apply { textSize = 18f }
        val settingsButton = Button(this).apply {
            text = "Open Notification Access Settings"
            setOnClickListener {
                startActivity(Intent(Settings.ACTION_NOTIFICATION_LISTENER_SETTINGS))
            }
        }
        val listHeading = TextView(this).apply {
            text = "Latest captured Google Pay notifications"
            textSize = 18f
            setPadding(0, dp(20), 0, dp(8))
        }
        notificationsList = TextView(this).apply {
            textIsSelectable = true
            textSize = 14f
        }

        val content = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            setPadding(dp(20), dp(24), dp(20), dp(24))
            addView(accessStatus, matchWidth())
            addView(settingsButton, matchWidth())
            addView(listHeading, matchWidth())
            addView(notificationsList, matchWidth())
        }
        setContentView(ScrollView(this).apply { addView(content) })
    }

    override fun onResume() {
        super.onResume()
        if (!receiverRegistered) {
            ContextCompat.registerReceiver(
                this,
                notificationsChangedReceiver,
                IntentFilter(CapturedNotificationStore.ACTION_NOTIFICATIONS_CHANGED),
                ContextCompat.RECEIVER_NOT_EXPORTED,
            )
            receiverRegistered = true
        }
        refreshScreen()
    }

    override fun onPause() {
        if (receiverRegistered) {
            unregisterReceiver(notificationsChangedReceiver)
            receiverRegistered = false
        }
        super.onPause()
    }

    private fun refreshScreen() {
        val accessEnabled = packageName in NotificationManagerCompat.getEnabledListenerPackages(this)
        accessStatus.text = "Notification access: ${if (accessEnabled) "Enabled" else "Disabled"}"

        val notifications = CapturedNotificationStore(this).latest().take(10)
        notificationsList.text = if (notifications.isEmpty()) {
            "No Google Pay notifications captured yet."
        } else {
            notifications.joinToString(separator = "\n\n──────────────\n\n") { it.toDebugText() }
        }
    }

    private fun PaymentNotificationSnapshot.toDebugText(): String = buildString {
        appendLine("Package: $packageName")
        appendLine("Title: ${title ?: "null"}")
        appendLine("Text: ${text ?: "null"}")
        appendLine("BigText: ${bigText ?: "null"}")
        appendLine("SubText: ${subText ?: "null"}")
        appendLine("Post time: ${DateFormat.format("yyyy-MM-dd HH:mm:ss z", Date(postTime))} ($postTime)")
        append("Notification key: ${notificationKey ?: "null"}")
    }

    private fun matchWidth() = LinearLayout.LayoutParams(
        ViewGroup.LayoutParams.MATCH_PARENT,
        ViewGroup.LayoutParams.WRAP_CONTENT,
    )

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
