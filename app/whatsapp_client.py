import logging
import httpx
from app.config import settings

logger = logging.getLogger(__name__)


async def _send_request(path: str, payload: dict):
    if not settings.EVOLUTION_API_URL or not settings.EVOLUTION_API_KEY or not settings.EVOLUTION_INSTANCE:
        logger.warning("Evolution API is not configured. Would have sent: %s", payload)
        return {"status": "simulated"}

    url = f"{settings.EVOLUTION_API_URL}{path}"
    headers = {
        "apikey": settings.EVOLUTION_API_KEY,
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(url, json=payload, headers=headers)
        if response.status_code >= 400:
            logger.error("Evolution API error %s: %s", response.status_code, response.text)
        response.raise_for_status()
        return response.json()


async def send_text(to_wa_id: str, body: str):
    payload = {
        "number": to_wa_id,
        "text": body,
    }
    return await _send_request(
        f"/message/sendText/{settings.EVOLUTION_INSTANCE}",
        payload,
    )


async def send_buttons(to_wa_id: str, body: str, buttons: list):
    # Evolution testing uses a plain-text fallback so onboarding works
    # without depending on provider-specific interactive-button payloads.
    options = "\n".join(f"{i + 1}. {title}" for i, title in enumerate(buttons))
    return await send_text(
        to_wa_id,
        f"{body}\n\n{options}\n\nPlease reply with 1 or 2.",
    )
