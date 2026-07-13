import httpx
import logging
from app.config import settings

logger = logging.getLogger(__name__)

GRAPH_BASE = f"https://graph.facebook.com/{settings.WHATSAPP_API_VERSION or 'v20.0'}"


async def send_text(to_wa_id: str, body: str):
    url = f"{GRAPH_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "text",
        "text": {"body": body}
    }
    await _send_request(url, payload)


async def send_buttons(to_wa_id: str, body: str, buttons: list):
    url = f"{GRAPH_BASE}/{settings.WHATSAPP_PHONE_NUMBER_ID}/messages"
    payload = {
        "messaging_product": "whatsapp",
        "to": to_wa_id,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": body},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": f"btn_{i}", "title": title}}
                    for i, title in enumerate(buttons)
                ]
            }
        }
    }
    await _send_request(url, payload)


async def _send_request(url: str, payload: dict):
    if not settings.WHATSAPP_TOKEN or not settings.WHATSAPP_PHONE_NUMBER_ID:
        logger.warning("WhatsApp not configured. Would have sent: %s", payload)
        return {"status": "simulated"}

    headers = {
        "Authorization": f"Bearer {settings.WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient() as client:
        resp = await client.post(url, json=payload, headers=headers)
        if resp.status_code >= 400:
            logger.error("WhatsApp API error: %s", resp.text)
        resp.raise_for_status()
        return resp.json()
