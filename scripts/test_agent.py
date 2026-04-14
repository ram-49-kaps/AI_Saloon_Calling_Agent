"""
Test script — simulates Vapi webhook tool calls against the local server.

Usage:
    python scripts/test_agent.py

This simulates the exact JSON payloads Vapi sends during a phone call,
hitting POST /api/vapi/webhook with tool-calls messages.
"""

import httpx
import json
import sys
from datetime import datetime, timedelta

BASE_URL = "http://localhost:80"
WEBHOOK = f"{BASE_URL}/api/vapi/webhook"

# ANSI colors
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
BOLD = "\033[1m"
RESET = "\033[0m"

passed = 0
failed = 0


def make_tool_call_payload(tool_name: str, arguments: dict, call_id: str = "test_001"):
    """Create the exact JSON structure Vapi sends for a tool call."""
    return {
        "message": {
            "type": "tool-calls",
            "toolCallList": [
                {
                    "id": call_id,
                    "function": {
                        "name": tool_name,
                        "arguments": arguments,
                    }
                }
            ]
        }
    }


def print_test(name: str, result: str, success: bool, details: str = ""):
    global passed, failed
    icon = f"{GREEN}✅ PASS{RESET}" if success else f"{RED}❌ FAIL{RESET}"
    print(f"\n{icon}  {BOLD}{name}{RESET}")
    print(f"   {CYAN}Response:{RESET} {result[:200]}")
    if details:
        print(f"   {YELLOW}Note:{RESET} {details}")
    if success:
        passed += 1
    else:
        failed += 1


def send(tool_name: str, arguments: dict, call_id: str = "test_001") -> dict:
    """Send a tool call and return the parsed response."""
    payload = make_tool_call_payload(tool_name, arguments, call_id)
    resp = httpx.post(WEBHOOK, json=payload, timeout=10)
    resp.raise_for_status()
    return resp.json()


def get_result_text(response: dict) -> str:
    """Extract the result text from the webhook response."""
    results = response.get("results", [])
    if results:
        return results[0].get("result", "")
    return str(response)


# ──────────────────────────────────────────────
# Calculate test dates
# ──────────────────────────────────────────────
tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
day_after = (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
past_date = (datetime.now() - timedelta(days=5)).strftime("%Y-%m-%d")
# Book at 3:00 PM tomorrow
book_time = (datetime.now() + timedelta(days=1)).replace(hour=15, minute=0, second=0, microsecond=0).isoformat()
# Reschedule to 4:00 PM day after
reschedule_time = (datetime.now() + timedelta(days=2)).replace(hour=16, minute=0, second=0, microsecond=0).isoformat()


print(f"\n{'='*60}")
print(f"{BOLD}{CYAN}🧪  SALON BOOKING AI AGENT — FULL TEST SUITE{RESET}")
print(f"{'='*60}")
print(f"   Server:  {BASE_URL}")
print(f"   Test dates:  tomorrow={tomorrow}, day_after={day_after}")
print(f"{'='*60}")


# ──────────────────────────────────────────────
# TEST 1: Health Check
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 1. HEALTH CHECK ──{RESET}")
try:
    resp = httpx.get(f"{BASE_URL}/")
    data = resp.json()
    print_test("GET /", json.dumps(data), data.get("status") == "ok")
except Exception as e:
    print_test("GET /", str(e), False, "Server not running?")


# ──────────────────────────────────────────────
# TEST 2: Check Availability — Valid Service
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 2. CHECK AVAILABILITY ──{RESET}")
try:
    resp = send("checkAvailability", {"service": "Haircut", "date": tomorrow})
    result = get_result_text(resp)
    print_test(
        "checkAvailability — Haircut tomorrow",
        result,
        "available slots" in result.lower() or "slot" in result.lower(),
    )
except Exception as e:
    print_test("checkAvailability — Haircut", str(e), False)

# ──────────────────────────────────────────────
# TEST 3: Check Availability — Fuzzy Hindi alias
# ──────────────────────────────────────────────
try:
    resp = send("checkAvailability", {"service": "baal katna", "date": tomorrow})
    result = get_result_text(resp)
    print_test(
        "checkAvailability — Hindi alias 'baal katna'",
        result,
        "haircut" in result.lower() or "slot" in result.lower(),
        "Tests multilingual fuzzy matching",
    )
except Exception as e:
    print_test("checkAvailability — Hindi alias", str(e), False)

# ──────────────────────────────────────────────
# TEST 4: Check Availability — Unknown Service
# ──────────────────────────────────────────────
try:
    resp = send("checkAvailability", {"service": "Laser Surgery", "date": tomorrow})
    result = get_result_text(resp)
    print_test(
        "checkAvailability — Unknown service 'Laser Surgery'",
        result,
        "couldn't find" in result.lower() or "we offer" in result.lower(),
        "Should list available services",
    )
except Exception as e:
    print_test("checkAvailability — Unknown service", str(e), False)

# ──────────────────────────────────────────────
# TEST 5: Check Availability — Past date
# ──────────────────────────────────────────────
try:
    resp = send("checkAvailability", {"service": "Facial", "date": past_date})
    result = get_result_text(resp)
    print_test(
        "checkAvailability — Past date rejected",
        result,
        "passed" in result.lower() or "past" in result.lower(),
    )
except Exception as e:
    print_test("checkAvailability — Past date", str(e), False)

# ──────────────────────────────────────────────
# TEST 6: Check Availability — Invalid date
# ──────────────────────────────────────────────
try:
    resp = send("checkAvailability", {"service": "Facial", "date": "not-a-date"})
    result = get_result_text(resp)
    print_test(
        "checkAvailability — Invalid date handled",
        result,
        "valid date" in result.lower() or "need" in result.lower(),
    )
except Exception as e:
    print_test("checkAvailability — Invalid date", str(e), False)


# ──────────────────────────────────────────────
# TEST 7: Book Appointment — Full flow
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 3. BOOK APPOINTMENT ──{RESET}")
booked_appointment_id = None
try:
    resp = send("bookAppointment", {
        "service": "Haircut",
        "start_time": book_time,
        "customer_name": "Test User",
        "phone": "9999900000",
    })
    result = get_result_text(resp)
    is_confirmed = "confirmed" in result.lower() or "appointment id" in result.lower()
    print_test("bookAppointment — Full booking", result, is_confirmed)

    # Extract appointment ID for later tests
    if "appointment ID is" in result:
        raw_id = result.split("appointment ID is")[-1].strip().rstrip(".")
        # Extract just the number
        booked_appointment_id = "".join(c for c in raw_id.split()[0] if c.isdigit())
        print(f"   {YELLOW}📋 Captured appointment ID: {booked_appointment_id}{RESET}")
except Exception as e:
    print_test("bookAppointment — Full booking", str(e), False)

# ──────────────────────────────────────────────
# TEST 8: Book Appointment — Missing fields
# ──────────────────────────────────────────────
try:
    resp = send("bookAppointment", {
        "service": "Haircut",
        "start_time": book_time,
        # missing name & phone
    })
    result = get_result_text(resp)
    print_test(
        "bookAppointment — Missing name & phone",
        result,
        "need" in result.lower() or "missing" in result.lower() or "still" in result.lower(),
    )
except Exception as e:
    print_test("bookAppointment — Missing fields", str(e), False)

# ──────────────────────────────────────────────
# TEST 9: Double-booking — Same slot should fail
# ──────────────────────────────────────────────
try:
    # Book 3 appointments at the same time to exhaust all stylists
    for i in range(3):
        send("bookAppointment", {
            "service": "Haircut",
            "start_time": book_time,
            "customer_name": f"Exhaust User {i}",
            "phone": f"888800000{i}",
        })

    # This one should fail — all stylists busy
    resp = send("bookAppointment", {
        "service": "Haircut",
        "start_time": book_time,
        "customer_name": "Overflow User",
        "phone": "7777700000",
    })
    result = get_result_text(resp)
    print_test(
        "bookAppointment — Overbooking protection",
        result,
        "not available" in result.lower() or "sorry" in result.lower(),
        "All stylists should be occupied at this time",
    )
except Exception as e:
    print_test("bookAppointment — Overbooking", str(e), False)


# ──────────────────────────────────────────────
# TEST 10: Get Customer Appointments
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 4. GET CUSTOMER APPOINTMENTS ──{RESET}")
try:
    resp = send("getCustomerAppointments", {"phone": "9999900000"})
    result = get_result_text(resp)
    print_test(
        "getCustomerAppointments — Booked user",
        result,
        "upcoming" in result.lower() or "haircut" in result.lower(),
    )
except Exception as e:
    print_test("getCustomerAppointments", str(e), False)

try:
    resp = send("getCustomerAppointments", {"phone": "0000000000"})
    result = get_result_text(resp)
    print_test(
        "getCustomerAppointments — Unknown phone",
        result,
        "don't have" in result.lower() or "no" in result.lower(),
    )
except Exception as e:
    print_test("getCustomerAppointments — Unknown phone", str(e), False)


# ──────────────────────────────────────────────
# TEST 11: Reschedule Appointment
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 5. RESCHEDULE APPOINTMENT ──{RESET}")
if booked_appointment_id:
    try:
        resp = send("rescheduleAppointment", {
            "appointment_id": booked_appointment_id,
            "new_time": reschedule_time,
        })
        result = get_result_text(resp)
        # Extract new ID
        new_id = None
        if "appointment ID is" in result:
            new_id = result.split("appointment ID is")[-1].strip().rstrip(".")
        print_test(
            "rescheduleAppointment — Valid reschedule",
            result,
            "rescheduled" in result.lower(),
        )
        if new_id:
            booked_appointment_id = new_id
            print(f"   {YELLOW}📋 New appointment ID after reschedule: {new_id}{RESET}")
    except Exception as e:
        print_test("rescheduleAppointment", str(e), False)
else:
    print_test("rescheduleAppointment", "Skipped (no appointment ID from booking)", False,
               "Previous booking test must pass first")

# ──────────────────────────────────────────────
# TEST 12: Reschedule — Invalid ID
# ──────────────────────────────────────────────
try:
    resp = send("rescheduleAppointment", {
        "appointment_id": "99999",
        "new_time": reschedule_time,
    })
    result = get_result_text(resp)
    print_test(
        "rescheduleAppointment — Invalid ID",
        result,
        "couldn't find" in result.lower() or "not" in result.lower(),
    )
except Exception as e:
    print_test("rescheduleAppointment — Invalid ID", str(e), False)


# ──────────────────────────────────────────────
# TEST 13: Cancel Appointment
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 6. CANCEL APPOINTMENT ──{RESET}")
if booked_appointment_id:
    try:
        resp = send("cancelAppointment", {"appointment_id": booked_appointment_id})
        result = get_result_text(resp)
        print_test(
            "cancelAppointment — By ID",
            result,
            "cancelled" in result.lower() or "canceled" in result.lower(),
        )
    except Exception as e:
        print_test("cancelAppointment — By ID", str(e), False)

    # Try cancelling same appointment again (should fail)
    try:
        resp = send("cancelAppointment", {"appointment_id": booked_appointment_id})
        result = get_result_text(resp)
        print_test(
            "cancelAppointment — Already cancelled (idempotent)",
            result,
            "couldn't find" in result.lower() or "no" in result.lower(),
        )
    except Exception as e:
        print_test("cancelAppointment — Already cancelled", str(e), False)
else:
    print_test("cancelAppointment", "Skipped (no appointment ID)", False)

# ──────────────────────────────────────────────
# TEST 14: Cancel — Missing info
# ──────────────────────────────────────────────
try:
    resp = send("cancelAppointment", {})
    result = get_result_text(resp)
    print_test(
        "cancelAppointment — No ID or phone",
        result,
        "need" in result.lower() or "appointment id" in result.lower() or "phone" in result.lower(),
    )
except Exception as e:
    print_test("cancelAppointment — No info", str(e), False)


# ──────────────────────────────────────────────
# TEST 15: Unknown Tool
# ──────────────────────────────────────────────
print(f"\n{BOLD}── 7. EDGE CASES ──{RESET}")
try:
    resp = send("nonExistentTool", {"foo": "bar"})
    result = get_result_text(resp)
    print_test(
        "Unknown tool name handled gracefully",
        result,
        "can't handle" in result.lower() or "sorry" in result.lower(),
    )
except Exception as e:
    print_test("Unknown tool", str(e), False)

# ──────────────────────────────────────────────
# TEST 16: Non-tool-call message types
# ──────────────────────────────────────────────
try:
    resp = httpx.post(WEBHOOK, json={
        "message": {"type": "status-update", "status": "in-progress"}
    }, timeout=10)
    data = resp.json()
    print_test(
        "status-update message type",
        json.dumps(data),
        data.get("ok") is True,
    )
except Exception as e:
    print_test("status-update message type", str(e), False)

try:
    resp = httpx.post(WEBHOOK, json={
        "message": {"type": "end-of-call-report", "report": {"duration": 45, "summary": "Test call"}}
    }, timeout=10)
    data = resp.json()
    print_test(
        "end-of-call-report message type",
        json.dumps(data),
        data.get("ok") is True,
    )
except Exception as e:
    print_test("end-of-call-report message type", str(e), False)


# ──────────────────────────────────────────────
# SUMMARY
# ──────────────────────────────────────────────
total = passed + failed
print(f"\n{'='*60}")
print(f"{BOLD}📊  TEST RESULTS{RESET}")
print(f"{'='*60}")
print(f"   {GREEN}Passed: {passed}{RESET}")
print(f"   {RED}Failed: {failed}{RESET}")
print(f"   Total:  {total}")
print(f"{'='*60}")

if failed > 0:
    print(f"\n{RED}{BOLD}⚠️  Some tests failed! Review the output above.{RESET}")
    sys.exit(1)
else:
    print(f"\n{GREEN}{BOLD}🎉  All tests passed! Your agent is working correctly.{RESET}")
    sys.exit(0)
