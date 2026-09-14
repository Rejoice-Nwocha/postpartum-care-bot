import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def _send_request(path: str, payload: dict):
    if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE:
        logger.warning("Evolution API is not configured; message was not sent")
        return {"status": "not_configured"}

    url = f"{settings.EVOLUTION_API_URL}{path}"
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            logger.error("Evolution API error %s: %s", response.status_code, response.text[:500])
        response.raise_for_status()
        return response.json()


async def send_text(to_wa_id: str, body: str):
    if not to_wa_id or not body:
        raise ValueError("Recipient and message body are required")

    payload = {
        "number": to_wa_id,
        "text": body,
    }
    return await _send_request(
        f"/message/sendText/{settings.EVOLUTION_INSTANCE}",
        payload,
    )


async def send_buttons(to_wa_id: str, body: str, buttons: list):
    # Keep the UX provider-independent while we test Evolution. The numbered
    # fallback also works on WhatsApp clients that do not render interactions.
    options = "\n".join(f"{i + 1}. {title}" for i, title in enumerate(buttons))
    return await send_text(to_wa_id, f"{body}\n\n{options}\n\nReply with the number of your choice.")
