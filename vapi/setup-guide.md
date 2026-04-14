# Vapi Setup Guide — Salon Booking AI Agent

## Prerequisites
- FastAPI backend running and accessible via a public URL
- Groq API key (free at https://console.groq.com)

---

## Step 1: Sign Up for Vapi

1. Go to [https://vapi.ai](https://vapi.ai)
2. Click "Get Started" → Sign up with Google/Email
3. You'll get **$10 free credit** (~200 minutes of calls)

---

## Step 2: Get a Groq API Key (FREE)

1. Go to [https://console.groq.com](https://console.groq.com)
2. Sign up with Google/GitHub
3. Go to "API Keys" → Create new key
4. Copy the key — you'll add it in Vapi

---

## Step 3: Add Groq Provider in Vapi

1. In Vapi dashboard → Go to **"Provider Keys"** (left sidebar)
2. Click **"Add Provider Key"**
3. Select **"Groq"**
4. Paste your Groq API key
5. Save

---

## Step 4: Create the Assistant

### Option A: Via Dashboard (Easy)
1. Go to **"Assistants"** → **"Create Assistant"**
2. Set the name: `Salon Booking Assistant`
3. **Model**: Select Groq → `llama-3.3-70b-versatile`
4. **System Prompt**: Copy the system prompt from `assistant-config.json`
5. **First Message**: "Hello! Welcome to our salon. How can I help you today?"
6. **Voice**: Select ElevenLabs → Rachel (or any natural-sounding voice)
7. **Server URL**: Enter your backend URL: `https://your-backend.com/api/vapi/webhook`

### Option B: Via API (Programmatic)
```bash
curl -X POST https://api.vapi.ai/assistant \
  -H "Authorization: Bearer YOUR_VAPI_API_KEY" \
  -H "Content-Type: application/json" \
  -d @assistant-config.json
```

---

## Step 5: Add Tools

In the assistant settings → **"Tools"** section:
1. Add each tool from `assistant-config.json`:
   - `checkAvailability`
   - `bookAppointment`
   - `cancelAppointment`
   - `rescheduleAppointment`
   - `getCustomerAppointments`
2. Each tool's Server URL should point to your backend webhook

---

## Step 6: Get a Phone Number

1. Go to **"Phone Numbers"** in Vapi dashboard
2. Click **"Buy Number"**
3. Select a US number (cheapest, ~$1/month)
4. Assign it to your **Salon Booking Assistant**
5. That's it! Calls to this number → AI agent answers directly

---

## Step 7: Test It!

1. Call the phone number from your phone
2. The AI agent will greet you
3. Try: "I want to book a haircut for tomorrow at 3 PM"
4. Check your PostgreSQL database — you should see the appointment!

---

## Step 8: Expose Your Local Backend (for testing)

If running FastAPI locally, use ngrok to expose it:

```bash
# Install ngrok
brew install ngrok

# Run your FastAPI server
python main.py

# In another terminal, expose port 8000
ngrok http 8000

# Copy the ngrok URL (e.g., https://abc123.ngrok.io)
# Set it as Server URL in Vapi: https://abc123.ngrok.io/api/vapi/webhook
```

---

## Costs Summary

| Service | Cost |
|---------|------|
| Vapi | $10 free credit (~200 min) |
| Groq LLM | FREE (rate limited) |
| Phone Number | ~$1/month (US) |
| ElevenLabs Voice | Included in Vapi |

**Total to get started: $0** (using free credits)
