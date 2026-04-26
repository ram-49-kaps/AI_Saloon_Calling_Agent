"""Switch Vapi phone number from static assistantId to dynamic serverUrl mode.

When using serverUrl mode:
- Vapi sends an `assistant-request` webhook at the START of every call
- Our backend responds with the full assistant config including TODAY's date
- This ensures dates are ALWAYS correct (no more "April 19th" when today is April 27th)

Run: VAPI_API_KEY=... python scripts/switch_to_dynamic.py
"""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx

VAPI_API_KEY = os.getenv("VAPI_API_KEY", "").strip()
SERVER_URL = os.getenv(
    "VAPI_SERVER_URL",
    "https://ai-saloon-calling-agent.onrender.com/api/vapi/webhook",
).strip()

HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}


def get_phone_numbers() -> list:
    """Fetch all phone numbers from Vapi."""
    with httpx.Client(timeout=30) as client:
        response = client.get(
            "https://api.vapi.ai/phone-number",
            headers=HEADERS,
        )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to fetch phone numbers: {response.text}")
    return response.json()


def switch_to_server_url(phone_id: str) -> dict:
    """
    Switch a phone number from assistantId → serverUrl mode.
    
    This makes Vapi send an `assistant-request` webhook at the start of each call,
    allowing us to return a fresh system prompt with today's real date.
    """
    with httpx.Client(timeout=30) as client:
        response = client.patch(
            f"https://api.vapi.ai/phone-number/{phone_id}",
            headers=HEADERS,
            json={
                "assistantId": None,         # Remove static assistant
                "serverUrl": SERVER_URL,      # Use dynamic server URL instead
            },
        )
    if response.status_code != 200:
        raise RuntimeError(f"Failed to update phone number: {response.text}")
    return response.json()


def main():
    if not VAPI_API_KEY:
        raise RuntimeError("Set VAPI_API_KEY before running this script.")

    print("📞 Fetching Vapi phone numbers...")
    phone_numbers = get_phone_numbers()

    if not phone_numbers:
        print("❌ No phone numbers found in your Vapi account.")
        return

    print(f"   Found {len(phone_numbers)} phone number(s):\n")

    for pn in phone_numbers:
        pn_id = pn.get("id", "unknown")
        number = pn.get("number", pn.get("name", "unknown"))
        current_assistant = pn.get("assistantId", "None")
        current_server = pn.get("serverUrl", "None")

        print(f"   📱 {number}")
        print(f"      ID: {pn_id}")
        print(f"      Current assistantId: {current_assistant}")
        print(f"      Current serverUrl: {current_server}")
        print()

    # Switch all phone numbers to serverUrl mode
    for pn in phone_numbers:
        pn_id = pn.get("id")
        number = pn.get("number", pn.get("name", "unknown"))

        if pn.get("serverUrl") == SERVER_URL and not pn.get("assistantId"):
            print(f"   ✅ {number} — already in serverUrl mode, skipping.")
            continue

        print(f"   🔄 Switching {number} to serverUrl mode...")
        result = switch_to_server_url(pn_id)
        print(f"   ✅ Done! serverUrl → {result.get('serverUrl', SERVER_URL)}")
        print(f"      assistantId → {result.get('assistantId', 'None (removed)')}")
        print()

    print("\n🎉 All phone numbers now use dynamic mode!")
    print("   Every call will get a FRESH system prompt with today's correct date.")
    print(f"   Webhook URL: {SERVER_URL}")


if __name__ == "__main__":
    main()
