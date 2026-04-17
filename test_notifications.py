"""Regression tests for booking, cancellation, and reschedule notifications."""

import unittest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, patch

from models.appointment import Appointment
from models.service import Service
from models.stylist import Stylist
from services.tools import book_appointment, cancel_appointment, reschedule_appointment


IST = timezone(timedelta(hours=5, minutes=30))


class FakeResult:
    def __init__(self, value):
        self.value = value

    def scalars(self):
        return self

    def all(self):
        return self.value

    def scalar(self):
        return self.value

    def scalar_one_or_none(self):
        return self.value


class FakeDB:
    def __init__(self, results):
        self.results = list(results)
        self.added = []

    async def execute(self, _statement):
        if self.results:
            return self.results.pop(0)
        return FakeResult(None)

    def add(self, obj):
        if getattr(obj, "id", None) is None:
            obj.id = 100 + len(self.added) + 1
        self.added.append(obj)

    async def flush(self):
        return None


class NotificationFlowTests(unittest.IsolatedAsyncioTestCase):
    async def test_booking_sends_sms_email_and_push(self):
        service = Service(
            name="Haircut",
            aliases=["hair cut", "વાળ કાપવા"],
            duration=30,
            price=500,
            category="Hair",
        )
        stylist = Stylist(
            name="Rahul",
            phone="9999999999",
            specializations=["Hair"],
            work_start="09:00",
            work_end="20:00",
            days_off=[],
            is_active=True,
        )
        start_time = (datetime.now(IST) + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0)
        db = FakeDB([
            FakeResult([service]),
            FakeResult([stylist]),
            FakeResult(0),
            FakeResult(0),
            FakeResult(None),
        ])

        with (
            patch("services.tools.send_booking_confirmation_sms", new=AsyncMock()) as sms_mock,
            patch("services.tools.send_booking_notification_email", new=AsyncMock()) as email_mock,
            patch("services.tools.send_admin_push_notification", new=AsyncMock()) as push_mock,
        ):
            result = await book_appointment(
                {
                    "service": "Haircut",
                    "start_time": start_time.isoformat(),
                    "customer_name": "Test User",
                    "phone": "9999900000",
                },
                db,
            )

        self.assertIn("confirmed", result.lower())
        sms_mock.assert_awaited_once()
        email_mock.assert_awaited_once()
        push_mock.assert_awaited_once()

    async def test_cancellation_sends_sms_and_email(self):
        appointment = Appointment(
            id=12,
            service_id=1,
            stylist_id=1,
            customer_name="Test User",
            customer_phone="9999900000",
            start_time=datetime.now(IST) + timedelta(days=1, hours=2),
            end_time=datetime.now(IST) + timedelta(days=1, hours=2, minutes=30),
            status="booked",
        )
        service = Service(
            id=1,
            name="Haircut",
            aliases=["hair cut"],
            duration=30,
            price=500,
            category="Hair",
        )
        db = FakeDB([
            FakeResult(appointment),
            FakeResult(service),
        ])

        with (
            patch("services.tools.send_cancellation_sms", new=AsyncMock()) as sms_mock,
            patch("services.tools.send_cancellation_notification_email", new=AsyncMock()) as email_mock,
        ):
            result = await cancel_appointment({"appointment_id": "12"}, db)

        self.assertEqual(appointment.status, "cancelled")
        self.assertIn("cancelled successfully", result.lower())
        sms_mock.assert_awaited_once()
        email_mock.assert_awaited_once()

    async def test_reschedule_sends_sms_and_email(self):
        old_appointment = Appointment(
            id=18,
            service_id=1,
            stylist_id=1,
            customer_name="Test User",
            customer_phone="9999900000",
            start_time=(datetime.now(IST) + timedelta(days=1)).replace(hour=11, minute=0, second=0, microsecond=0),
            end_time=(datetime.now(IST) + timedelta(days=1)).replace(hour=11, minute=30, second=0, microsecond=0),
            status="booked",
        )
        service = Service(
            id=1,
            name="Haircut",
            aliases=["hair cut"],
            duration=30,
            price=500,
            category="Hair",
        )
        stylist = Stylist(
            id=2,
            name="Amit",
            phone="9999999998",
            specializations=["Hair"],
            work_start="09:00",
            work_end="20:00",
            days_off=[],
            is_active=True,
        )
        new_time = (datetime.now(IST) + timedelta(days=2)).replace(hour=16, minute=0, second=0, microsecond=0)
        db = FakeDB([
            FakeResult(old_appointment),
            FakeResult(service),
            FakeResult([stylist]),
            FakeResult(0),
            FakeResult(0),
        ])

        with (
            patch("services.tools.send_reschedule_sms", new=AsyncMock()) as sms_mock,
            patch("services.tools.send_reschedule_notification_email", new=AsyncMock()) as email_mock,
        ):
            result = await reschedule_appointment(
                {
                    "appointment_id": "18",
                    "new_time": new_time.isoformat(),
                },
                db,
            )

        self.assertEqual(old_appointment.status, "rescheduled")
        self.assertIn("rescheduled", result.lower())
        sms_mock.assert_awaited_once()
        email_mock.assert_awaited_once()


if __name__ == "__main__":
    unittest.main()
