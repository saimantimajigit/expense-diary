package com.expensediary.android.notification

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNotEquals
import org.junit.Assert.assertNull
import org.junit.Test

class GooglePayNotificationParserTest {
    private val parser = GooglePayNotificationParser()

    @Test
    fun preservesAllRawGooglePayNotificationFields() {
        val notification = PaymentNotificationSnapshot(
            packageName = GooglePayNotificationParser.GOOGLE_PAY_PACKAGE,
            title = "Payment successful",
            text = "₹1,250 paid to Example Shop",
            bigText = "Full notification text",
            subText = "Google Pay",
            postTime = 1_798_853_700_000,
            notificationKey = "gpay|notification-key",
        )

        assertEquals(notification, parser.parse(notification))
    }

    @Test
    fun ignoresNotificationsFromOtherPackages() {
        val notification = PaymentNotificationSnapshot(
            packageName = "com.example.other",
            title = "Payment successful",
            text = "Some text",
            bigText = null,
            subText = null,
            postTime = 1_798_853_700_000,
            notificationKey = "other|notification-key",
        )

        assertNull(parser.parse(notification))
    }

    @Test
    fun duplicateIdentityIsStableAndChangesWhenNotificationContentChanges() {
        val notification = PaymentNotificationSnapshot(
            packageName = GooglePayNotificationParser.GOOGLE_PAY_PACKAGE,
            title = "Payment successful",
            text = "₹1,250 paid to Example Shop",
            bigText = null,
            subText = null,
            postTime = 1_798_853_700_000,
            notificationKey = "gpay|notification-key",
        )

        assertEquals(notification.duplicateKey(), notification.copy().duplicateKey())
        assertNotEquals(notification.duplicateKey(), notification.copy(text = "Updated text").duplicateKey())
    }
}
