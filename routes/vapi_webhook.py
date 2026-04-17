"""Vapi webhook route — receives tool calls and call reports from Vapi AI agent."""

import logging
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from database import get_db
from services.tools import TOOL_HANDLERS
from middleware.vapi_auth import verify_vapi_secret
from models.call_log import CallLog
from services.sms_service import send_sms

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/vapi", tags=["Vapi Webhook"])


@router.post("/webhook")
async def vapi_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    _: None = Depends(verify_vapi_secret),
):
    """
    Main webhook endpoint that Vapi calls during a phone conversation.

    Handles message types:
    - tool-calls: Dispatches to the appropriate tool handler and returns results
    - end-of-call-report: Stores call analytics and sends feedback SMS
    - status-update: Tracks call status
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    message = body.get("message", {})
    msg_type = message.get("type", "")

    logger.info(f"Vapi webhook received: type={msg_type}")

    if msg_type == "assistant-request":
        from utils.prompt import get_system_prompt
        logger.info("Serving dynamic assistant-request response with current date.")
        return {
            "assistant": {
                "model": {
                    "systemPrompt": get_system_prompt()
                }
            }
        }

    # Handle tool calls from the AI agent
    if msg_type == "tool-calls":
        return await _handle_tool_calls(message, db)

    # Handle end of call report — store analytics + send feedback SMS
    elif msg_type == "end-of-call-report":
        await _handle_call_report(message, db)
        return {"ok": True}

    # Handle status updates
    elif msg_type == "status-update":
        status = message.get("status", "unknown")
        logger.info(f"Call status update: {status}")
        return {"ok": True}

    # For any other message types, acknowledge
    return {"ok": True}


async def _handle_tool_calls(message: dict, db: AsyncSession) -> dict:
    """
    Process tool calls from Vapi and return results.

    Vapi sends tool calls in this format:
    {
        "type": "tool-calls",
        "toolCallList": [
            {
                "id": "call_xxx",
                "function": {
                    "name": "checkAvailability",
                    "arguments": { "service": "Haircut", "date": "2026-04-15" }
                }
            }
        ]
    }

    We must return:
    {
        "results": [
            {
                "toolCallId": "call_xxx",
                "result": "Available slots: 10:00 AM, 11:30 AM..."
            }
        ]
    }
    """
    tool_calls = message.get("toolCallList", [])
    results = []

    for tool_call in tool_calls:
        call_id = tool_call.get("id", "")
        function = tool_call.get("function", {})
        tool_name = function.get("name", "")
        arguments = function.get("arguments", {})

        print(f"🔧 Tool call: {tool_name} | args: {arguments}")

        # Dispatch to the correct handler
        handler = TOOL_HANDLERS.get(tool_name)
        if handler:
            try:
                result = await handler(arguments, db)
            except Exception as e:
                logger.error(f"Tool handler error for {tool_name}: {e}")
                result = "Sorry, something went wrong. Please try again."
        else:
            logger.warning(f"Unknown tool called: {tool_name}")
            result = "Sorry, I can't handle that request right now."

        results.append({
            "toolCallId": call_id,
            "result": result,
        })

    return {"results": results}


async def _handle_call_report(message: dict, db: AsyncSession) -> None:
    """
    Store call analytics from end-of-call-report and send feedback SMS.

    This is the core of the feedback loop — every call is logged so we can:
    1. Track booking success rates
    2. Identify failed calls
    3. Collect customer feedback via SMS
    4. Improve the prompt based on real data
    """
    # Vapi sends the report at the top level or nested under "report"
    report = message.get("report", message)

    call_id = report.get("callId", report.get("call", {}).get("id", "unknown"))
    duration = report.get("duration", report.get("durationSeconds", 0))
    cost = report.get("cost", 0)
    ended_reason = report.get("endedReason", "unknown")
    transcript = report.get("transcript", "")
    summary = report.get("summary", "")

    # Extract phone number from call metadata
    call_data = report.get("call", {})
    phone_number = call_data.get("customer", {}).get("number", "")

    # Extract timestamps
    started_at_str = call_data.get("startedAt", "")
    started_at = None
    if started_at_str:
        try:
            started_at = datetime.fromisoformat(started_at_str.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    # Count tool calls and detect if booking succeeded
    messages = report.get("messages", report.get("artifact", {}).get("messages", []))
    tool_calls_count = 0
    tool_errors_count = 0
    booking_succeeded = False

    for msg in messages:
        if msg.get("role") == "tool_calls" or msg.get("type") == "tool-calls":
            tool_calls_count += 1
        if msg.get("role") == "tool_call_result" or msg.get("type") == "tool-call-result":
            result_text = str(msg.get("content", "") or msg.get("result", ""))
            if "appointment is confirmed" in result_text.lower():
                booking_succeeded = True
            if "error" in result_text.lower() or "sorry" in result_text.lower():
                tool_errors_count += 1

    # Also check the transcript text directly
    if isinstance(transcript, str) and "appointment is confirmed" in transcript.lower():
        booking_succeeded = True

    # Store in database
    call_log = CallLog(
        vapi_call_id=str(call_id),
        phone_number=phone_number,
        duration_seconds=float(duration) if duration else 0,
        cost=float(cost) if cost else 0,
        ended_reason=ended_reason,
        transcript=transcript if isinstance(transcript, str) else str(transcript),
        summary=summary,
        booking_succeeded=booking_succeeded,
        tool_calls_count=tool_calls_count,
        tool_errors_count=tool_errors_count,
        call_started_at=started_at,
    )

    db.add(call_log)
    await db.flush()

    logger.info(
        f"📊 Call logged: id={call_log.id} call={call_id} "
        f"duration={duration}s booked={booking_succeeded} "
        f"tools={tool_calls_count} errors={tool_errors_count}"
    )

    # Send feedback SMS if a booking was made and we have a phone number
    if booking_succeeded and phone_number:
        clean_phone = "".join(filter(str.isdigit, phone_number))
        if len(clean_phone) >= 10:
            feedback_msg = (
                f"Thanks for booking with us! "
                f"How was your experience? Reply with a number 1-5 "
                f"(1=Bad, 5=Excellent). Your feedback helps us improve!"
            )
            sms_sent = await send_sms(clean_phone, feedback_msg)
            if sms_sent:
                call_log.feedback_sent = True
                logger.info(f"📬 Feedback SMS sent to {clean_phone}")


@router.post("/feedback")
async def receive_feedback(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """
    Endpoint to receive customer feedback ratings.

    Can be called by:
    - Twilio webhook (when customer replies to feedback SMS)
    - Admin dashboard manually
    """
    try:
        # Handle Twilio incoming SMS webhook format
        form = await request.form()
        body_text = form.get("Body", "").strip()
        from_number = form.get("From", "").strip()

        if not body_text or not from_number:
            # Try JSON format (for admin/manual input)
            try:
                json_data = await request.json()
                body_text = str(json_data.get("rating", ""))
                from_number = json_data.get("phone", "")
            except Exception:
                raise HTTPException(status_code=400, detail="Missing rating or phone")

        # Parse rating (1-5)
        try:
            rating = int(body_text.strip()[0])  # Take first digit
            if rating < 1 or rating > 5:
                raise ValueError
        except (ValueError, IndexError):
            return {"ok": True}  # Ignore non-rating messages

        # Find the most recent call log for this phone number
        clean_phone = "".join(filter(str.isdigit, from_number))
        result = await db.execute(
            select(CallLog)
            .where(CallLog.phone_number.contains(clean_phone[-10:]))
            .order_by(CallLog.created_at.desc())
            .limit(1)
        )
        call_log = result.scalar_one_or_none()

        if call_log:
            call_log.feedback_rating = rating
            logger.info(f"⭐ Feedback received: {rating}/5 for call {call_log.vapi_call_id}")

            # Send thank you
            if rating >= 4:
                await send_sms(clean_phone, "Thank you for the great rating! We look forward to seeing you! 😊")
            elif rating <= 2:
                await send_sms(clean_phone, "We're sorry about your experience. We'll work on improving. Thank you for your feedback!")
            else:
                await send_sms(clean_phone, "Thank you for your feedback! We're always working to improve.")
        else:
            logger.warning(f"Feedback from {from_number} but no matching call log found")

        return {"ok": True}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback processing error: {e}")
        return {"ok": True}
