"""Email service — sends appointment confirmation emails via SMTP (Gmail/Brevo)."""

import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import settings

logger = logging.getLogger(__name__)


def build_confirmation_email(
    customer_name: str,
    customer_email: str,
    service_name: str,
    stylist_name: str,
    date_str: str,
    time_str: str,
    appointment_id: int,
    duration: int,
    price: float,
) -> MIMEMultipart:
    """Build a styled confirmation email."""
    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"✅ Appointment Confirmed — {service_name} on {date_str}"
    msg["From"] = f"Salon Booking <{settings.SMTP_FROM_EMAIL}>"
    msg["To"] = customer_email

    html = f"""
    <html>
    <body style="font-family: 'Segoe UI', Arial, sans-serif; background: #f5f5f5; padding: 20px;">
      <div style="max-width: 500px; margin: auto; background: #fff; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
        <div style="background: linear-gradient(135deg, #667eea, #764ba2); padding: 24px; text-align: center;">
          <h1 style="color: #fff; margin: 0; font-size: 22px;">✂️ Appointment Confirmed!</h1>
        </div>
        <div style="padding: 24px;">
          <p style="font-size: 16px; color: #333;">Hi <strong>{customer_name}</strong>,</p>
          <p style="color: #555;">Your salon appointment has been booked successfully. Here are the details:</p>

          <table style="width: 100%; border-collapse: collapse; margin: 16px 0;">
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888; width: 40%;">📋 Service</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">{service_name}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888;">📅 Date</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">{date_str}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888;">⏰ Time</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">{time_str}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888;">💇 Stylist</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">{stylist_name}</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888;">⏱️ Duration</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">{duration} minutes</td>
            </tr>
            <tr style="border-bottom: 1px solid #eee;">
              <td style="padding: 10px 0; color: #888;">💰 Price</td>
              <td style="padding: 10px 0; font-weight: bold; color: #333;">₹{int(price)}</td>
            </tr>
            <tr>
              <td style="padding: 10px 0; color: #888;">🆔 Appointment ID</td>
              <td style="padding: 10px 0; font-weight: bold; color: #667eea; font-size: 18px;">{appointment_id}</td>
            </tr>
          </table>

          <div style="background: #f0f4ff; border-radius: 8px; padding: 12px; margin-top: 16px;">
            <p style="margin: 0; font-size: 13px; color: #555;">
              ⚠️ <strong>Cancellation Policy:</strong> Appointments can be cancelled up to 1 hour before the scheduled time.
              To cancel or reschedule, call us and provide your Appointment ID.
            </p>
          </div>

          <p style="margin-top: 20px; color: #666; font-size: 14px;">Thank you for choosing our salon! See you soon. 😊</p>
        </div>
        <div style="background: #fafafa; padding: 12px; text-align: center; font-size: 12px; color: #999;">
          Salon Booking AI Agent • Powered by Vapi
        </div>
      </div>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))
    return msg


async def send_confirmation_email(
    customer_name: str,
    customer_email: str,
    service_name: str,
    stylist_name: str,
    date_str: str,
    time_str: str,
    appointment_id: int,
    duration: int,
    price: float,
) -> bool:
    """Send booking confirmation email. Returns True on success."""
    if not settings.SMTP_HOST or not settings.SMTP_FROM_EMAIL:
        print("⚠️  Email not configured (SMTP_HOST missing). Skipping email.")
        return False

    try:
        msg = build_confirmation_email(
            customer_name=customer_name,
            customer_email=customer_email,
            service_name=service_name,
            stylist_name=stylist_name,
            date_str=date_str,
            time_str=time_str,
            appointment_id=appointment_id,
            duration=duration,
            price=price,
        )

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_FROM_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)

        print(f"📧 Confirmation email sent to {customer_email}")
        return True

    except Exception as e:
        print(f"❌ Failed to send email: {e}")
        return False
