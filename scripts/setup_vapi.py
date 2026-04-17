"""Update the Vapi assistant with multilingual salon settings."""

from __future__ import annotations

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import httpx
from utils.prompt import get_system_prompt


VAPI_API_KEY = os.getenv("VAPI_API_KEY", "").strip()
ASSISTANT_ID = os.getenv("VAPI_ASSISTANT_ID", "").strip()
SERVER_URL = os.getenv(
    "VAPI_SERVER_URL",
    "https://ai-saloon-calling-agent.onrender.com/api/vapi/webhook",
).strip()

TRANSCRIBER_PROVIDER = os.getenv("VAPI_TRANSCRIBER_PROVIDER", "deepgram").strip().lower()
TRANSCRIBER_MODEL = os.getenv("VAPI_TRANSCRIBER_MODEL", "").strip()
TRANSCRIBER_LANGUAGE = os.getenv("VAPI_TRANSCRIBER_LANGUAGE", "").strip()

VOICE_PROVIDER = os.getenv("VAPI_VOICE_PROVIDER", "azure").strip().lower()
VOICE_ID = os.getenv("VAPI_VOICE_ID", "").strip()


HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

SYSTEM_PROMPT = get_system_prompt()

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "checkAvailability",
            "description": "Check available appointment slots for a salon service on a specific date, optionally for a specific stylist. Always call this before booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The salon service name.",
                    },
                    "date": {
                        "type": "string",
                        "description": "The date to check in YYYY-MM-DD format.",
                    },
                    "stylist_name": {
                        "type": "string",
                        "description": "Optional preferred stylist name.",
                    },
                },
                "required": ["service", "date"],
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "type": "function",
        "function": {
            "name": "bookAppointment",
            "description": "Book a confirmed appointment. Only call this after the customer confirms all details.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {"type": "string"},
                    "start_time": {
                        "type": "string",
                        "description": "ISO 8601 datetime for the appointment start.",
                    },
                    "customer_name": {"type": "string"},
                    "phone": {
                        "type": "string",
                        "description": "10-digit phone number without spaces or dashes.",
                    },
                    "preferred_stylist": {
                        "type": "string",
                        "description": "Optional preferred stylist name.",
                    },
                },
                "required": ["service", "start_time", "customer_name", "phone"],
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "type": "function",
        "function": {
            "name": "cancelAppointment",
            "description": "Cancel an appointment by appointment ID or by customer phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"},
                    "phone": {"type": "string"},
                },
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "type": "function",
        "function": {
            "name": "rescheduleAppointment",
            "description": "Reschedule an existing appointment to a new ISO 8601 datetime.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {"type": "string"},
                    "new_time": {"type": "string"},
                },
                "required": ["appointment_id", "new_time"],
            },
        },
        "server": {"url": SERVER_URL},
    },
    {
        "type": "function",
        "function": {
            "name": "getCustomerAppointments",
            "description": "Look up a customer's upcoming appointments using their phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {"type": "string"},
                },
                "required": ["phone"],
            },
        },
        "server": {"url": SERVER_URL},
    },
]


def build_transcriber() -> dict:
    """Build the transcriber configuration for Vapi."""
    if TRANSCRIBER_PROVIDER == "google":
        return {
            "provider": "google",
            "model": TRANSCRIBER_MODEL or "latest",
            "language": TRANSCRIBER_LANGUAGE or "multilingual",
        }

    if TRANSCRIBER_PROVIDER == "deepgram":
        return {
            "provider": "deepgram",
            "model": TRANSCRIBER_MODEL or "nova-3",
            "language": TRANSCRIBER_LANGUAGE or "multi",
            "keywords": [
                "rahul:3",
                "priya:3",
                "amit:3",
                "haircut:2",
                "facial:2",
                "manicure:2",
                "pedicure:2",
                "threading:2",
            ],
            "keyterm": [
                "Hair Spa",
                "Hair Color",
                "Beard Trim",
            ],
        }

    raise ValueError(f"Unsupported VAPI_TRANSCRIBER_PROVIDER: {TRANSCRIBER_PROVIDER}")


def build_voice() -> dict:
    """Build the voice configuration for Vapi."""
    if VOICE_PROVIDER == "azure":
        return {
            "provider": "azure",
            "voiceId": VOICE_ID or "en-US-JennyNeural",
            "speed": 0.9,
        }

    if VOICE_PROVIDER in {"11labs", "elevenlabs"}:
        return {
            "provider": "11labs",
            "voiceId": VOICE_ID or "21m00Tcm4TlvDq8ikWAM",
        }

    raise ValueError(f"Unsupported VAPI_VOICE_PROVIDER: {VOICE_PROVIDER}")


def setup() -> None:
    """Set up the Vapi assistant with safe multilingual defaults."""
    if not VAPI_API_KEY or not ASSISTANT_ID:
        raise RuntimeError("Set VAPI_API_KEY and VAPI_ASSISTANT_ID before running this script.")

    transcriber = build_transcriber()
    voice = build_voice()

    if transcriber["provider"] == "deepgram":
        print("⚠️  Deepgram nova-3 multi handles Hindi well, but Gujarati coverage is weaker than Google multilingual.")
        print("   For reliable Gujarati calls, prefer VAPI_TRANSCRIBER_PROVIDER=google.")

    update_data = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o",
            "systemPrompt": SYSTEM_PROMPT,
            "tools": TOOLS,
        },
        "voice": voice,
        "transcriber": transcriber,
        "firstMessage": "Hello! Welcome to our salon. How can I help you today?",
        "firstMessageMode": "assistant-speaks-first",
        "serverUrl": SERVER_URL,
        "startSpeakingPlan": {
            "waitSeconds": 0.8,
            "smartEndpointingEnabled": "livekit"
        },
        "serverMessages": [
            "tool-calls",
            "end-of-call-report",
            "status-update",
            "hang"
        ]
    }

    with httpx.Client(timeout=30) as client:
        print("🔧 Updating Vapi Assistant...")
        response = client.patch(
            f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
            headers=HEADERS,
            json=update_data,
        )

    if response.status_code != 200:
        raise RuntimeError(f"Vapi update failed ({response.status_code}): {response.text}")

    data = response.json()
    print("✅ Assistant updated successfully!")
    print(f"   Assistant: {data.get('name', 'N/A')}")
    print(f"   Server URL: {data.get('serverUrl', 'N/A')}")
    print(f"   Transcriber: {transcriber['provider']} / {transcriber['model']}")
    print(f"   Voice: {voice['provider']} / {voice['voiceId']}")


if __name__ == "__main__":
    setup()
