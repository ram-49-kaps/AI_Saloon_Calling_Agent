"""Quick test — send a real SMS via Twilio to verify the service works."""

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.sms_service import send_sms
from config import settings


async def main():
    print("=" * 50)
    print("📱  SMS Service Test (Twilio)")
    print("=" * 50)
    print(f"  Account SID:   {'✅ ' + settings.TWILIO_ACCOUNT_SID[:8] + '...' if settings.TWILIO_ACCOUNT_SID else '❌ MISSING'}")
    print(f"  Auth Token:    {'✅ Set' if settings.TWILIO_AUTH_TOKEN else '❌ MISSING'}")
    print(f"  Twilio Phone:  {settings.TWILIO_PHONE_NUMBER or '❌ MISSING'}")
    print(f"  Owner Phone:   {settings.SALON_OWNER_PHONE or '❌ MISSING'}")
    print("=" * 50)

    # Send a test SMS to the salon owner's phone
    test_phone = settings.SALON_OWNER_PHONE
    test_message = (
        "Test from Salon Booking Agent!\n"
        "If you received this, your SMS service is working.\n"
        "- Salon Booking AI"
    )

    print(f"\n🚀 Sending test SMS to +91{test_phone}...")
    result = await send_sms(test_phone, test_message)
    print(f"\n{'✅ SUCCESS — Check your phone!' if result else '❌ FAILED — See error above'}")


if __name__ == "__main__":
    asyncio.run(main())
