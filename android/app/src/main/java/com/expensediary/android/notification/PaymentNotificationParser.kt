package com.expensediary.android.notification

import java.security.MessageDigest

/** Raw values supplied by Android's NotificationListenerService callback. */
data class PaymentNotificationSnapshot(
    val packageName: String,
    val title: String?,
    val text: String?,
    val bigText: String?,
    val subText: String?,
    val postTime: Long,
    val notificationKey: String?,
) {
    /** Stable identity for suppressing repeated callbacks for the same notification. */
    fun duplicateKey(): String {
        val raw = listOf(
            packageName,
            notificationKey.orEmpty(),
            postTime.toString(),
            title.orEmpty(),
            text.orEmpty(),
            bigText.orEmpty(),
            subText.orEmpty(),
        ).joinToString("\u0000")
        return MessageDigest.getInstance("SHA-256")
            .digest(raw.toByteArray(Charsets.UTF_8))
            .joinToString("") { byte -> "%02x".format(byte.toInt() and 0xff) }
    }
}

/** Keeps platform notification access separate from app-specific recognition. */
interface PaymentNotificationParser {
    fun parse(notification: PaymentNotificationSnapshot): PaymentNotificationSnapshot?
}

/** For this discovery milestone, Google Pay notifications remain completely unparsed. */
class GooglePayNotificationParser : PaymentNotificationParser {
    override fun parse(notification: PaymentNotificationSnapshot): PaymentNotificationSnapshot? =
        notification.takeIf { it.packageName == GOOGLE_PAY_PACKAGE }

    companion object {
        const val GOOGLE_PAY_PACKAGE = "com.google.android.apps.nbu.paisa.user"
    }
}
