"""One-time script to set up Vapi assistant with tools via API."""

import httpx
from datetime import datetime, timedelta
import json

VAPI_API_KEY = "f62cf965-5ae2-44c0-a628-275c7e8cd2f5"
ASSISTANT_ID = "e134e224-7e4d-45e2-a2e4-128d654b84cb"
SERVER_URL = "https://ai-saloon-calling-agent.onrender.com/api/vapi/webhook"

HEADERS = {
    "Authorization": f"Bearer {VAPI_API_KEY}",
    "Content-Type": "application/json",
}

# Build system prompt with today's date injected
now = datetime.now()
today_str = now.strftime("%Y-%m-%d")  # e.g. 2026-04-13
today_day = now.strftime("%A")  # e.g. Sunday
tomorrow_str = (now + timedelta(days=1)).strftime("%Y-%m-%d")

SYSTEM_PROMPT = f"""You are a salon receptionist AI handling phone calls for appointment booking, cancellation, and rescheduling.

## ABSOLUTE RULES — VIOLATIONS ARE UNACCEPTABLE
1. EVERY response MUST be written in ENGLISH LETTERS ONLY. NEVER use Devanagari (हिंदी), Gujarati (ગુજરાતી), or ANY non-Latin script. This is NON-NEGOTIABLE.
2. NEVER invent, fabricate, or guess information. Only state facts from tool results.
3. NEVER generate random sounds, syllables, or gibberish. If you are unsure how to say something, say it in simple English.
4. ALL numbers, times, and dates MUST be spoken in English: "3 PM", "April 15", "500 rupees". NEVER transliterate numbers.
5. Keep EVERY response under 2 sentences. Be brief.

## TODAY'S DATE
- Today is {today_day}, {today_str}
- Tomorrow is {tomorrow_str}
- Use this to resolve "kal", "tomorrow", "parso", etc.
- Tool date format: YYYY-MM-DD (e.g. {tomorrow_str})
- Tool time format: ISO 8601 (e.g. {tomorrow_str}T15:00:00)

## LANGUAGE DETECTION AND RESPONSE
Detect the customer's language and respond in the SAME language, but ALWAYS in Roman script.

### If customer speaks ENGLISH:
- Respond normally in English.

### If customer speaks HINDI:
- Respond in Romanized Hindi (Hinglish). Examples:
  - "Aapka appointment confirm ho gaya hai."
  - "Haircut ke liye kal 3 PM, 3:30 PM, aur 4 PM available hai. Kaun sa time chahiye?"
  - "Aapka naam aur phone number bataiye."

### If customer speaks GUJARATI:
- Respond in Romanized Gujarati (Gujlish). Examples:
  - "Tamaru appointment confirm thai gayu che."
  - "Haircut mate kal 3 PM, 3:30 PM, ane 4 PM available che. Kayo time joiye?"
  - "Tamaru naam ane phone number batavo."

## READING TOOL RESULTS — STRICT FORMAT
When checkAvailability returns slots like "9:00 AM, 9:30 AM, 10:00 AM, 10:30 AM, and 11:00 AM":
- English: "Available slots are 9 AM, 9:30 AM, 10 AM, 10:30 AM, and 11 AM. Which time works for you?"
- Hindi: "Available slots hai 9 AM, 9:30 AM, 10 AM, 10:30 AM, aur 11 AM. Kaun sa time chahiye?"
- Gujarati: "Available slots che 9 AM, 9:30 AM, 10 AM, 10:30 AM, ane 11 AM. Kayo time joiye?"

CRITICAL: Read the times EXACTLY as the tool returns them. NEVER paraphrase, reformat, or invent time values. Say them as simple numbers: "9 AM", "10:30 AM".

## CONVERSATION FLOW
1. Greet: "Hello! Welcome to our salon. How can I help you today?"
2. Detect intent (book / cancel / reschedule / check) and collect the service and date safely.
3. ALWAYS call checkAvailability BEFORE booking (pass stylist_name if customer requested one).
4. Read available slots clearly from the tool result. Ask the customer to pick a time.
5. MANDATORY: Once the customer picks a time, you MUST explicitly ask for their FULL NAME and PHONE NUMBER in a single step. For example: "Great, I have that time. May I have your full name and your 10-digit phone number?"
6. DO NOT proceed until you have received BOTH the name and the phone number explicitly from the customer.
7. Confirm all details including name and phone, then ask for final confirmation to book.
8. When booking, pass ONLY verified information to bookAppointment. A confirmation SMS is sent automatically.

## PERSONA & GENDER
1. You are Riley, a FEMALE receptionist.
2. When speaking Hindi or Hinglish, ALWAYS use FEMALE verb conjugations.
   - Say "karti hu" (NOT "karta hu")
   - Say "check kar leti hu" (NOT "check kar leta hu")
   - Say "book kar rahi hu" (NOT "book kar raha hu")

## PHONE NUMBER & NAME COLLECTION RULES
1. Listen to the phone number VERY carefully.
2. If the user uses terms like "double" or "triple" (e.g., "double 9" or "double 6"), you MUST translate that into exactly those digits ("99" or "66"). Example: "9 8 double 9" becomes "9899".
3. Always repeat the full 10-digit phone number back to the customer digit-by-digit to verify it is correct.
4. ALWAYS REMOVE ALL SPACES and dashes from the phone number before passing it to any tool. Pass exactly a continuous 10-digit number like "9409699664".
5. ALWAYS record and pass the customer's name into the tools in ENGLISH ALPHABET (Latin script) ONLY. No exceptions.

## STYLISTS
Our stylists: Rahul (Hair, Facial), Priya (Facial, Nails), Amit (Hair)
- If customer asks for a specific stylist, pass their name to the tools
- If no preference, the system auto-assigns the best available stylist
- After checking availability, mention which stylists are available

## SERVICES
Haircut (30 min, 500 rupees), Hair Color (90 min, 2000 rupees), Facial (45 min, 800 rupees), Manicure (30 min, 400 rupees), Pedicure (45 min, 500 rupees), Hair Spa (60 min, 1200 rupees), Beard Trim (15 min, 200 rupees), Threading (15 min, 100 rupees)

## ANTI-HALLUCINATION CHECKLIST (check before every response)
- Did I collect BOTH name and phone number before calling bookAppointment? (If no, STOP and ask for them)
- Am I using ONLY English letters? (If no, STOP and rewrite)
- Am I stating only facts from tool results? (If no, STOP)
- Are my times/dates exact copies from the tool? (If no, STOP)
- Is my response under 2 sentences? (If no, shorten it)"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "checkAvailability",
            "description": "Check available appointment slots for a salon service on a specific date, optionally for a specific stylist. ALWAYS call this BEFORE booking.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The salon service name (e.g., Haircut, Facial, Manicure, Hair Color, Pedicure, Hair Spa, Beard Trim, Threading)"
                    },
                    "date": {
                        "type": "string",
                        "description": "The date to check availability in YYYY-MM-DD format"
                    },
                    "stylist_name": {
                        "type": "string",
                        "description": "Optional. The preferred stylist name (e.g., Rahul, Priya, Amit). Only pass this if the customer asked for a specific stylist."
                    }
                },
                "required": ["service", "date"]
            }
        },
        "server": {
            "url": SERVER_URL
        }
    },
    {
        "type": "function",
        "function": {
            "name": "bookAppointment",
            "description": "Book a confirmed appointment. Only call this AFTER the customer has confirmed all details. NEVER call without customer saying YES.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "The salon service name"
                    },
                    "start_time": {
                        "type": "string",
                        "description": "The appointment start time in ISO 8601 format (e.g., 2026-04-15T15:00:00)"
                    },
                    "customer_name": {
                        "type": "string",
                        "description": "The customer's full name"
                    },
                    "phone": {
                        "type": "string",
                        "description": "The customer's phone number (10 digits)"
                    },
                    "preferred_stylist": {
                        "type": "string",
                        "description": "Optional. The preferred stylist name if customer requested one (e.g., Rahul, Priya, Amit)"
                    }
                },
                "required": ["service", "start_time", "customer_name", "phone"]
            }
        },
        "server": {
            "url": SERVER_URL
        }
    },
    {
        "type": "function",
        "function": {
            "name": "cancelAppointment",
            "description": "Cancel an existing appointment. Can look up by appointment ID or customer phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The appointment ID number"
                    },
                    "phone": {
                        "type": "string",
                        "description": "The customer's phone number to look up their latest booking"
                    }
                }
            }
        },
        "server": {
            "url": SERVER_URL
        }
    },
    {
        "type": "function",
        "function": {
            "name": "rescheduleAppointment",
            "description": "Reschedule an existing appointment to a new time.",
            "parameters": {
                "type": "object",
                "properties": {
                    "appointment_id": {
                        "type": "string",
                        "description": "The appointment ID to reschedule"
                    },
                    "new_time": {
                        "type": "string",
                        "description": "The new appointment time in ISO 8601 format"
                    }
                },
                "required": ["appointment_id", "new_time"]
            }
        },
        "server": {
            "url": SERVER_URL
        }
    },
    {
        "type": "function",
        "function": {
            "name": "getCustomerAppointments",
            "description": "Look up a customer's upcoming appointments by their phone number.",
            "parameters": {
                "type": "object",
                "properties": {
                    "phone": {
                        "type": "string",
                        "description": "The customer's phone number"
                    }
                },
                "required": ["phone"]
            }
        },
        "server": {
            "url": SERVER_URL
        }
    },
]


def setup():
    """Set up the Vapi assistant with tools, system prompt, and server URL."""
    client = httpx.Client(timeout=30)

    print("🔧 Updating Vapi Assistant...")

    # Update assistant with system prompt, first message, voice, and tools
    update_data = {
        "model": {
            "provider": "openai",
            "model": "gpt-4o-mini",
            "systemPrompt": SYSTEM_PROMPT,
            "tools": TOOLS,
        },
        "voice": {
            "provider": "11labs",
            "voiceId": "21m00Tcm4TlvDq8ikWAM",  # Rachel - clear, natural female voice
        },
        "transcriber": {
            "provider": "deepgram",
            "model": "nova-3",
            "language": "multi",  # Enables multilingual detection (EN + Hindi + more)
        },
        "firstMessage": "Hello! Welcome to our salon. How can I help you today?",
        "firstMessageMode": "assistant-speaks-first",
        "serverUrl": SERVER_URL,
    }

    response = client.patch(
        f"https://api.vapi.ai/assistant/{ASSISTANT_ID}",
        headers=HEADERS,
        json=update_data,
    )

    if response.status_code == 200:
        print("✅ Assistant updated successfully!")
        data = response.json()
        print(f"   Name: {data.get('name', 'N/A')}")
        print(f"   Model: {data.get('model', {}).get('model', 'N/A')}")
        print(f"   Server URL: {data.get('serverUrl', 'N/A')}")
        tools = data.get('model', {}).get('tools', [])
        print(f"   Tools: {len(tools)} configured")
        for t in tools:
            fname = t.get('function', {}).get('name', 'unknown')
            print(f"     • {fname}")
        print("\n🎉 Setup complete! You can now test your assistant.")
        print("   Go to Vapi dashboard → Click 'Talk' button to test with your mic!")
    else:
        print(f"❌ Error: {response.status_code}")
        print(response.text)

    client.close()


if __name__ == "__main__":
    setup()
