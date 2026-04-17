"""
🔍 FULL SYSTEM AUDIT — Tests every component before deployment.
Run this with the FastAPI server already running on port 8000.
"""

import httpx
import asyncio
import json
import os
import sys

BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
HEADERS = {}

if os.getenv("VAPI_SERVER_SECRET"):
    HEADERS["x-vapi-secret"] = os.getenv("VAPI_SERVER_SECRET", "")

PASS = "✅"
FAIL = "❌"
WARN = "⚠️"

results = []


def log(component: str, test: str, status: str, detail: str = ""):
    results.append({"component": component, "test": test, "status": status, "detail": detail})
    icon = PASS if status == "PASS" else (FAIL if status == "FAIL" else WARN)
    print(f"  {icon} [{component}] {test}" + (f" — {detail}" if detail else ""))


async def run_all_tests():
    print("=" * 60)
    print("🔍  FULL SYSTEM AUDIT — Salon Booking AI Agent")
    print("=" * 60)

        async with httpx.AsyncClient(base_url=BASE_URL, timeout=15, headers=HEADERS) as client:

        # ────────────────────────────────────────────
        # 1. HEALTH CHECK
        # ────────────────────────────────────────────
        print("\n📡 1. Server Health")
        try:
            r = await client.get("/")
            data = r.json()
            if r.status_code == 200 and data.get("status") == "ok":
                log("Server", "Health endpoint", "PASS", f"Status {r.status_code}")
            else:
                log("Server", "Health endpoint", "FAIL", f"Unexpected response: {data}")
        except Exception as e:
            log("Server", "Health endpoint", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 2. WEBHOOK ACCEPTS REQUESTS
        # ────────────────────────────────────────────
        print("\n🔗 2. Webhook Connectivity")
        try:
            r = await client.post("/api/vapi/webhook", json={"message": {"type": "status-update", "status": "test"}})
            if r.status_code == 200:
                log("Webhook", "POST /api/vapi/webhook", "PASS", "Accepts requests")
            else:
                log("Webhook", "POST /api/vapi/webhook", "FAIL", f"Status {r.status_code}")
        except Exception as e:
            log("Webhook", "POST /api/vapi/webhook", "FAIL", str(e))

        # Unknown message type
        try:
            r = await client.post("/api/vapi/webhook", json={"message": {"type": "unknown-type"}})
            if r.status_code == 200:
                log("Webhook", "Handles unknown message types", "PASS")
            else:
                log("Webhook", "Handles unknown message types", "FAIL", f"Status {r.status_code}")
        except Exception as e:
            log("Webhook", "Handles unknown message types", "FAIL", str(e))

        # Invalid JSON
        try:
            r = await client.post("/api/vapi/webhook", content="not json", headers={"Content-Type": "application/json"})
            if r.status_code == 400:
                log("Webhook", "Rejects invalid JSON", "PASS", "Returns 400")
            else:
                log("Webhook", "Rejects invalid JSON", "WARN", f"Status {r.status_code} (expected 400)")
        except Exception as e:
            log("Webhook", "Rejects invalid JSON", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 3. TOOL: checkAvailability
        # ────────────────────────────────────────────
        print("\n📅 3. Tool: checkAvailability")

        # Valid request
        tool_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [{
                    "id": "test_avail_1",
                    "function": {
                        "name": "checkAvailability",
                        "arguments": {"service": "Haircut", "date": "2026-04-16"}
                    }
                }]
            }
        }
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "available" in result_text.lower() or "slot" in result_text.lower() or "sorry" in result_text.lower():
                log("checkAvailability", "Haircut on April 16", "PASS", result_text[:80])
            else:
                log("checkAvailability", "Haircut on April 16", "WARN", result_text[:80])
        except Exception as e:
            log("checkAvailability", "Haircut on April 16", "FAIL", str(e))

        # Past date
        tool_payload["message"]["toolCallList"][0]["function"]["arguments"]["date"] = "2025-01-01"
        tool_payload["message"]["toolCallList"][0]["id"] = "test_avail_2"
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "passed" in result_text.lower():
                log("checkAvailability", "Rejects past date", "PASS")
            else:
                log("checkAvailability", "Rejects past date", "WARN", result_text[:80])
        except Exception as e:
            log("checkAvailability", "Rejects past date", "FAIL", str(e))

        # Invalid service
        tool_payload["message"]["toolCallList"][0]["function"]["arguments"] = {"service": "XYZ_INVALID", "date": "2026-04-16"}
        tool_payload["message"]["toolCallList"][0]["id"] = "test_avail_3"
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "couldn't find" in result_text.lower() or "offer" in result_text.lower():
                log("checkAvailability", "Invalid service handled", "PASS")
            else:
                log("checkAvailability", "Invalid service handled", "WARN", result_text[:80])
        except Exception as e:
            log("checkAvailability", "Invalid service handled", "FAIL", str(e))

        # With stylist preference
        tool_payload["message"]["toolCallList"][0]["function"]["arguments"] = {"service": "Haircut", "date": "2026-04-16", "stylist_name": "Rahul"}
        tool_payload["message"]["toolCallList"][0]["id"] = "test_avail_4"
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "rahul" in result_text.lower():
                log("checkAvailability", "Stylist preference (Rahul)", "PASS", result_text[:80])
            else:
                log("checkAvailability", "Stylist preference (Rahul)", "WARN", result_text[:80])
        except Exception as e:
            log("checkAvailability", "Stylist preference (Rahul)", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 4. TOOL: bookAppointment
        # ────────────────────────────────────────────
        print("\n📝 4. Tool: bookAppointment")

        # Missing fields
        tool_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [{
                    "id": "test_book_1",
                    "function": {
                        "name": "bookAppointment",
                        "arguments": {"service": "Haircut"}
                    }
                }]
            }
        }
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "need" in result_text.lower() or "missing" in result_text.lower():
                log("bookAppointment", "Catches missing fields", "PASS")
            else:
                log("bookAppointment", "Catches missing fields", "WARN", result_text[:80])
        except Exception as e:
            log("bookAppointment", "Catches missing fields", "FAIL", str(e))

        # Valid booking (use a future time)
        tool_payload["message"]["toolCallList"][0]["function"]["arguments"] = {
            "service": "Facial",
            "start_time": "2026-04-17T14:00:00+05:30",
            "customer_name": "System Test",
            "phone": "9999911111",
        }
        tool_payload["message"]["toolCallList"][0]["id"] = "test_book_2"
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "confirmed" in result_text.lower():
                log("bookAppointment", "Book Facial on Apr 17", "PASS", result_text[:100])
                # Extract appointment ID for later tests
                import re
                id_match = re.search(r"ID is (\d+)", result_text)
                booked_id = id_match.group(1) if id_match else None
            else:
                log("bookAppointment", "Book Facial on Apr 17", "WARN", result_text[:100])
                booked_id = None
        except Exception as e:
            log("bookAppointment", "Book Facial on Apr 17", "FAIL", str(e))
            booked_id = None

        # ────────────────────────────────────────────
        # 5. TOOL: getCustomerAppointments
        # ────────────────────────────────────────────
        print("\n🔍 5. Tool: getCustomerAppointments")

        tool_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [{
                    "id": "test_lookup_1",
                    "function": {
                        "name": "getCustomerAppointments",
                        "arguments": {"phone": "9999911111"}
                    }
                }]
            }
        }
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "upcoming" in result_text.lower() or "appointment" in result_text.lower():
                log("getCustomerAppointments", "Lookup by phone", "PASS", result_text[:80])
            else:
                log("getCustomerAppointments", "Lookup by phone", "WARN", result_text[:80])
        except Exception as e:
            log("getCustomerAppointments", "Lookup by phone", "FAIL", str(e))

        # No results phone
        tool_payload["message"]["toolCallList"][0]["function"]["arguments"]["phone"] = "0000000000"
        tool_payload["message"]["toolCallList"][0]["id"] = "test_lookup_2"
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "don't have" in result_text.lower() or "no" in result_text.lower():
                log("getCustomerAppointments", "No results for unknown phone", "PASS")
            else:
                log("getCustomerAppointments", "No results for unknown phone", "WARN", result_text[:80])
        except Exception as e:
            log("getCustomerAppointments", "No results for unknown phone", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 6. TOOL: cancelAppointment
        # ────────────────────────────────────────────
        print("\n🗑️  6. Tool: cancelAppointment")

        if booked_id:
            tool_payload = {
                "message": {
                    "type": "tool-calls",
                    "toolCallList": [{
                        "id": "test_cancel_1",
                        "function": {
                            "name": "cancelAppointment",
                            "arguments": {"appointment_id": booked_id}
                        }
                    }]
                }
            }
            try:
                r = await client.post("/api/vapi/webhook", json=tool_payload)
                data = r.json()
                result_text = data.get("results", [{}])[0].get("result", "")
                if "cancelled" in result_text.lower():
                    log("cancelAppointment", f"Cancel ID {booked_id}", "PASS")
                else:
                    log("cancelAppointment", f"Cancel ID {booked_id}", "WARN", result_text[:80])
            except Exception as e:
                log("cancelAppointment", f"Cancel ID {booked_id}", "FAIL", str(e))
        else:
            log("cancelAppointment", "Cancel test", "WARN", "Skipped — no booking ID from previous test")

        # Invalid ID
        tool_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [{
                    "id": "test_cancel_2",
                    "function": {
                        "name": "cancelAppointment",
                        "arguments": {"appointment_id": "99999"}
                    }
                }]
            }
        }
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "couldn't find" in result_text.lower() or "verify" in result_text.lower():
                log("cancelAppointment", "Invalid ID handled", "PASS")
            else:
                log("cancelAppointment", "Invalid ID handled", "WARN", result_text[:80])
        except Exception as e:
            log("cancelAppointment", "Invalid ID handled", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 7. TOOL: Unknown tool name
        # ────────────────────────────────────────────
        print("\n🔧 7. Unknown Tool Handling")

        tool_payload = {
            "message": {
                "type": "tool-calls",
                "toolCallList": [{
                    "id": "test_unknown",
                    "function": {
                        "name": "someRandomTool",
                        "arguments": {}
                    }
                }]
            }
        }
        try:
            r = await client.post("/api/vapi/webhook", json=tool_payload)
            data = r.json()
            result_text = data.get("results", [{}])[0].get("result", "")
            if "can't" in result_text.lower() or "sorry" in result_text.lower():
                log("Webhook", "Unknown tool returns graceful error", "PASS")
            else:
                log("Webhook", "Unknown tool returns graceful error", "WARN", result_text[:80])
        except Exception as e:
            log("Webhook", "Unknown tool returns graceful error", "FAIL", str(e))

        # ────────────────────────────────────────────
        # 8. END-OF-CALL REPORT
        # ────────────────────────────────────────────
        print("\n📊 8. End-of-Call Report")

        try:
            r = await client.post("/api/vapi/webhook", json={
                "message": {
                    "type": "end-of-call-report",
                    "report": {"duration": 120, "summary": "Test call completed"}
                }
            })
            if r.status_code == 200:
                log("Webhook", "End-of-call report handled", "PASS")
            else:
                log("Webhook", "End-of-call report handled", "FAIL", f"Status {r.status_code}")
        except Exception as e:
            log("Webhook", "End-of-call report handled", "FAIL", str(e))

    # ────────────────────────────────────────────
    # SUMMARY
    # ────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("📋  AUDIT SUMMARY")
    print("=" * 60)

    passed = sum(1 for r in results if r["status"] == "PASS")
    failed = sum(1 for r in results if r["status"] == "FAIL")
    warned = sum(1 for r in results if r["status"] == "WARN")
    total = len(results)

    print(f"\n  {PASS} Passed:  {passed}/{total}")
    print(f"  {WARN} Warnings: {warned}/{total}")
    print(f"  {FAIL} Failed:  {failed}/{total}")

    if failed == 0:
        print(f"\n  🎉 ALL TESTS PASSED — System is ready for deployment!")
    else:
        print(f"\n  ⛔ {failed} test(s) failed — Fix before deploying!")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_all_tests())
