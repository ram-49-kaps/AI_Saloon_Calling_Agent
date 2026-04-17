"""Email service — sends salon event notifications via SMTP."""

from __future__ import annotations

import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import settings

logger = logging.getLogger(__name__)


def _notification_recipients() -> list[str]:
    """Return the configured notification email recipients."""
    raw_values = [
        settings.SALON_OWNER_EMAIL,
        settings.SALON_NOTIFICATION_EMAILS,
    ]
    recipients: list[str] = []

    for raw in raw_values:
        if not raw:
            continue
        for value in raw.split(","):
            email = value.strip()
            if email and email not in recipients:
                recipients.append(email)

    return recipients


def _build_event_email(
    *,
    subject: str,
    heading: str,
    intro: str,
    accent_color: str,
    detail_rows: list[tuple[str, str]],
) -> MIMEMultipart:
    """Build a simple HTML email for salon staff notifications."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"Salon Booking <{settings.SMTP_FROM_EMAIL}>"

    rows_html = "".join(
        f"""
        <tr style="border-bottom: 1px solid #eee;">
          <td style="padding: 10px 0; color: #888; width: 38%;">{label}</td>
          <td style="padding: 10px 0; font-weight: 600; color: #333;">{value}</td>
        </tr>
        """
        for label, value in detail_rows
    )

    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 560px; margin: auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.08);">
        <div style="background: linear-gradient(135deg, {accent_color}, #1f2937); padding: 24px; text-align: center;">
          <h1 style="color: #fff; margin: 0; font-size: 22px;">{heading}</h1>
        </div>
        <div style="padding: 24px;">
          <p style="color: #555; font-size: 15px; margin-top: 0;">{intro}</p>
          <table style="width: 100%; border-collapse: collapse; margin: 18px 0;">
            {rows_html}
          </table>
        </div>
        <div style="background: #fafafa; padding: 12px; text-align: center; font-size: 12px; color: #999;">
          Salon Booking AI Agent
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))
    return msg


async def _send_to_recipients(msg: MIMEMultipart, recipients: list[str]) -> bool:
    """Send an email message to every configured recipient."""
    if not recipients:
        logger.info("No notification email recipients configured. Skipping email.")
        return False

    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        logger.info("Email not configured (SMTP_HOST / SMTP_FROM_EMAIL missing). Skipping email.")
        return False

    try:
        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            if settings.SMTP_USE_TLS:
                server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_FROM_EMAIL, settings.SMTP_PASSWORD)

            for recipient in recipients:
                msg["To"] = recipient
                server.send_message(msg)
                del msg["To"]

        logger.info("Email notifications sent to %s", ", ".join(recipients))
        return True
    except Exception as exc:
        logger.error("Failed to send email notifications: %s", exc)
        return False


async def send_booking_notification_email(
    *,
    customer_name: str,
    customer_phone: str,
    service_name: str,
    stylist_name: str,
    date_str: str,
    time_str: str,
    appointment_id: int,
    price: float,
) -> bool:
    """Send a booking notification email to the salon inbox."""
    msg = _build_event_email(
        subject=f"New Booking: {service_name} on {date_str}",
        heading="New Appointment Booked",
        intro="A new appointment has been confirmed through the calling agent.",
        accent_color="#2563eb",
        detail_rows=[
            ("Customer", customer_name),
            ("Phone", customer_phone),
            ("Service", service_name),
            ("Stylist", stylist_name),
            ("Date", date_str),
            ("Time", time_str),
            ("Price", f"Rs.{int(price)}"),
            ("Appointment ID", str(appointment_id)),
        ],
    )
    return await _send_to_recipients(msg, _notification_recipients())


async def send_cancellation_notification_email(
    *,
    customer_name: str,
    customer_phone: str,
    service_name: str,
    date_str: str,
    time_str: str,
    appointment_id: int,
) -> bool:
    """Send a cancellation notification email to the salon inbox."""
    msg = _build_event_email(
        subject=f"Cancelled: {service_name} on {date_str}",
        heading="Appointment Cancelled",
        intro="An existing appointment has been cancelled through the calling agent.",
        accent_color="#dc2626",
        detail_rows=[
            ("Customer", customer_name),
            ("Phone", customer_phone),
            ("Service", service_name),
            ("Date", date_str),
            ("Time", time_str),
            ("Appointment ID", str(appointment_id)),
        ],
    )
    return await _send_to_recipients(msg, _notification_recipients())


async def send_reschedule_notification_email(
    *,
    customer_name: str,
    customer_phone: str,
    service_name: str,
    stylist_name: str,
    old_date_str: str,
    old_time_str: str,
    new_date_str: str,
    new_time_str: str,
    old_appointment_id: int,
    new_appointment_id: int,
) -> bool:
    """Send a reschedule notification email to the salon inbox."""
    msg = _build_event_email(
        subject=f"Rescheduled: {service_name} to {new_date_str}",
        heading="Appointment Rescheduled",
        intro="An appointment has been moved to a new slot through the calling agent.",
        accent_color="#d97706",
        detail_rows=[
            ("Customer", customer_name),
            ("Phone", customer_phone),
            ("Service", service_name),
            ("Stylist", stylist_name),
            ("Old Slot", f"{old_date_str} at {old_time_str}"),
            ("New Slot", f"{new_date_str} at {new_time_str}"),
            ("Old Appointment ID", str(old_appointment_id)),
            ("New Appointment ID", str(new_appointment_id)),
        ],
    )
    return await _send_to_recipients(msg, _notification_recipients())
