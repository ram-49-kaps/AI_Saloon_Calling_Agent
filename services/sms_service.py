"""SMS service — sends booking notifications via Twilio."""

import httpx
import logging
import base64

from config import settings

logger = logging.getLogger(__name__)


async def send_sms(phone: str, message: str) -> bool:
    """Send an SMS via Twilio REST API. Returns True on success."""

    # Check if Twilio is configured
    if not settings.TWILIO_ACCOUNT_SID or not settings.TWILIO_AUTH_TOKEN or not settings.TWILIO_PHONE_NUMBER:
        print(f"\n" + "=" * 40)
        print(f"📱 [SIMULATED SMS to {phone}]")
        print(f"{message}")
        print("=" * 40 + "\n")
        print("⚠️  Twilio not configured. SMS Simulated.")
        return True

    # Format Indian phone number with country code
    phone = phone.strip().replace(" ", "").replace("-", "")
    if phone.startswith("+91"):
        pass  # Already formatted
    elif phone.startswith("91") and len(phone) == 12:
        phone = "+" + phone
    elif len(phone) == 10:
        phone = "+91" + phone

    # Always log to console
    print(f"\n" + "=" * 40)
    print(f"📱 [SMS to {phone}]")
    print(f"{message}")
    print("=" * 40 + "\n")

    try:
        # Twilio REST API — no SDK needed, just httpx
        url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"

        # Basic auth: Account SID : Auth Token
        auth_str = f"{settings.TWILIO_ACCOUNT_SID}:{settings.TWILIO_AUTH_TOKEN}"
        auth_b64 = base64.b64encode(auth_str.encode()).decode()

        async with httpx.AsyncClient(timeout=15) as client:
            response = await client.post(
                url,
                headers={
                    "Authorization": f"Basic {auth_b64}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={
                    "To": phone,
                    "From": settings.TWILIO_PHONE_NUMBER,
                    "Body": message,
                },
            )

            data = response.json()

            if response.status_code in (200, 201):
                sid = data.get("sid", "unknown")
                print(f"✅ SMS sent successfully! SID: {sid}")
                return True
            else:
                error_msg = data.get("message", "Unknown error")
                error_code = data.get("code", "N/A")
                print(f"❌ Twilio error ({error_code}): {error_msg}")
                return False

    except Exception as e:
        print(f"❌ SMS error: {e}")
        logger.error(f"SMS sending failed: {e}")
        return False


async def send_booking_confirmation_sms(
    customer_name: str,
    customer_phone: str,
    service_name: str,
    stylist_name: str,
    date_str: str,
    time_str: str,
    appointment_id: int,
    price: float,
) -> None:
    """Send dual SMS — one to customer, one to salon owner."""

    # SMS to Customer
    customer_msg = (
        f"Booking Confirmed!\n"
        f"Service: {service_name}\n"
        f"Date: {date_str}, {time_str}\n"
        f"Stylist: {stylist_name}\n"
        f"ID: {appointment_id}\n"
        f"Price: Rs.{int(price)}\n"
        f"To cancel, call us with your ID."
    )
    await send_sms(customer_phone, customer_msg)

    # SMS to Salon Owner
    if settings.SALON_OWNER_PHONE:
        owner_msg = (
            f"New Booking!\n"
            f"Customer: {customer_name} ({customer_phone})\n"
            f"Service: {service_name}\n"
            f"Date: {date_str}, {time_str}\n"
            f"Stylist: {stylist_name}\n"
            f"ID: {appointment_id}\n"
            f"Price: Rs.{int(price)}"
        )
        await send_sms(settings.SALON_OWNER_PHONE, owner_msg)


async def send_cancellation_sms(
    customer_name: str,
    customer_phone: str,
    service_name: str,
    appointment_id: int,
) -> None:
    """Send cancellation notification to customer + owner."""

    customer_msg = (
        f"Appointment Cancelled.\n"
        f"Service: {service_name}\n"
        f"ID: {appointment_id}\n"
        f"You can book again anytime by calling us."
    )
    await send_sms(customer_phone, customer_msg)

    if settings.SALON_OWNER_PHONE:
        owner_msg = (
            f"Booking Cancelled!\n"
            f"Customer: {customer_name} ({customer_phone})\n"
            f"Service: {service_name}\n"
            f"ID: {appointment_id}"
        )
        await send_sms(settings.SALON_OWNER_PHONE, owner_msg)
