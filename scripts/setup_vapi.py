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

VOICE_PROVIDER = os.getenv("VAPI_VOICE_PROVIDER", "cartesia").strip().lower()
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
            "description": "Book a confirmed appointment. IMPORTANT: You MUST call checkAvailability FIRST and confirm a time slot exists before calling this tool. NEVER call bookAppointment without first getting available slots from checkAvailability and having the customer pick a time.",
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
                "Haircut",
                "Hair Spa",
                "Hair Color",
                "Beard Trim",
            ],
        }

    raise ValueError(f"Unsupported VAPI_TRANSCRIBER_PROVIDER: {TRANSCRIBER_PROVIDER}")


def build_voice() -> dict:
    """Build the voice configuration for Vapi."""
    if VOICE_PROVIDER == "cartesia":
        # Cartesia Sonic-3 — ultra-low latency (<40ms), most human-like for phone calls
        return {
            "provider": "cartesia",
            "voiceId": VOICE_ID or "a0e99841-438c-4a64-b679-ae501e7d6091",  # Cartesia "Brooke" — natural, warm female
            "model": "sonic-2",
        }

    if VOICE_PROVIDER == "azure":
        return {
            "provider": "azure",
            "voiceId": VOICE_ID or "en-US-JennyNeural",
            "speed": 1.0,
        }

    if VOICE_PROVIDER in {"11labs", "elevenlabs"}:
        # ElevenLabs Sarah — warm, conversational, multilingual
        return {
            "provider": "11labs",
            "voiceId": VOICE_ID or "EXAVITQu4vr4xnSDxMaL",  # Sarah — natural, warm
            "stability": 0.4,  # Lower = more natural emotional variation
            "similarityBoost": 0.8,
            "speed": 1.0,  # Normal speed (was 0.9 — made it sound slow/robotic)
        }

    raise ValueError(f"Unsupported VAPI_VOICE_PROVIDER: {VOICE_PROVIDER}. Use 'cartesia', '11labs', or 'azure'.")


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
            "model": "gpt-4o-mini",  # Faster than gpt-4o for lower latency (~300ms vs ~600ms)
            "systemPrompt": SYSTEM_PROMPT,
            "tools": TOOLS,
            "temperature": 0.3,  # Lower = more consistent, less hallucination
            "maxTokens": 200,  # Short responses = faster delivery
        },
        "voice": voice,
        "transcriber": transcriber,
        "firstMessage": "Hi there! Welcome to our salon — how can I help you today?",
        "firstMessageMode": "assistant-speaks-first",
        "serverUrl": SERVER_URL,
        # === LATENCY TUNING ===
        "startSpeakingPlan": {
            "waitSeconds": 0.4,  # Reduced from 0.8 → 0.4 for near-instant response
            "smartEndpointingEnabled": True,  # ML-based detection of when user is done speaking
        },
        "stopSpeakingPlan": {
            "numWords": 0,  # Stop immediately when user interrupts (no overlap)
        },
        "silenceTimeoutSeconds": 20,  # Hang up after 20s silence
        "responseDelaySeconds": 0.1,  # Minimal delay before starting to speak
        "numWordsToInterruptAssistant": 2,  # User needs to say only 2 words to interrupt
        # === SERVER MESSAGES ===
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
