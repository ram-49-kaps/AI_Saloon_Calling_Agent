"""Vapi webhook route — receives tool calls from Vapi AI agent during phone calls."""

import logging

from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from database import get_db
from services.tools import TOOL_HANDLERS
from middleware.vapi_auth import verify_vapi_secret

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
    - end-of-call-report: Logs call analytics (optional)
    - status-update: Tracks call status (optional)
    """
    try:
        body = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON body")

    message = body.get("message", {})
    msg_type = message.get("type", "")

    logger.info(f"Vapi webhook received: type={msg_type}")

    # Handle tool calls from the AI agent
    if msg_type == "tool-calls":
        return await _handle_tool_calls(message, db)

    # Handle end of call report (logging)
    elif msg_type == "end-of-call-report":
        _log_call_report(message)
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


def _log_call_report(message: dict):
    """Log end-of-call analytics."""
    report = message.get("report", message)
    duration = report.get("duration", "unknown")
    summary = report.get("summary", "No summary")
    logger.info(f"Call ended. Duration: {duration}s. Summary: {summary}")
